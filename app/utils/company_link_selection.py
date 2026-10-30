"""
Link selection and ordering for company overview (box 2).
Direct links from official company sources only — selects up to 8 links in
strict priority order:
1. Company Website          (home)
2. About & Mission          (about) — about us / mission statement / goals
3. Official Social Media    (social) — company's "follow us" hub, or a verified profile
4. YouTube                  (youtube) — official channel, resolved to its featured video
5. Community Engagement     (community)
6. Recent News              (news)
7. Investor Relations       (investor)
8. Role-Specific Page       (role_specific) — department page, or the exec who owns it

Every slot is restricted to the company's own domain, except 'social'
(also allows verified social profiles) and 'youtube' (official YouTube
channel, which doesn't live on the company domain but is directly produced
by the company).

Slots are dropped if no qualifying link is found — no fillers. Missing slots
are simply skipped; the next slot in the order takes its place.
"""

__all__ = [
    'select_top_link_per_category',
    'order_by_priority',
    'select_additional_links'
]

import logging
import re
from urllib.parse import urlparse
from app.utils.company_queries import format_category_name, get_category_keywords
from app.utils.salary_link_selection import _company_name_strict, _normalize, _strict_name_forms
from app.utils.youtube_resolver import parse_channel_url, resolve_youtube_channel_to_video

logger = logging.getLogger(__name__)

SOCIAL_DOMAINS = {'facebook.com', 'instagram.com', 'x.com', 'twitter.com', 'tiktok.com', 'linkedin.com'}

PRIORITY_ORDER = ['home', 'about', 'social', 'youtube', 'community', 'news', 'investor', 'role_specific']

# What an official account may add after the company name: @WalmartCorporate,
# @RTXCorporation, c/HIIYouTube, @alphabetir, linkedin.com/company/kirkland-&-ellis-llp
HANDLE_SUFFIXES = {'', 'inc', 'corp', 'corporation', 'corporate', 'co', 'company', 'group', 'technologies',
                   'llp', 'llc', 'ltd', 'official', 'global', 'hq', 'us', 'usa', 'youtube', 'ir'}

# A channel *named* the company, give or take a legal suffix ("Mars, Incorporated")
CHANNEL_NAME_SUFFIX = re.compile(r' (incorporated|inc|corporation|corp|company|co|llp|llc|official)$')

# The title must say the page is about this topic — the domain match alone lets in
# subsidiaries ("General Dynamics Mission Systems") and products ("Chicken Stock")
SLOT_TITLE_MUST_MATCH = {
    'about': re.compile(r'about|who we are|our story|overview|our mission|mission statement|mission\s*(&|and)'
                        r'|our goals|our vision|our values|purpose|at a glance', re.I),
    'investor': re.compile(r'investor|financial|annual report|quarterly|sec filings?|earnings|stockholder'
                           r'|shareholder|10-k|results', re.I),
}

# On-domain pages that aren't about the company itself: law firms' client insights,
# alerts, practice pages and events; blog tag pages; customer support forums
SLOT_URL_EXCLUDE = re.compile(
    r'/insight|/publication|/pubs/|/practices?/|/services/|/events/|client-alert|client-news|/tag/'
    r'|//(support|discussions|forums?)\.|/support/|/thread/', re.I)

# Topics an overflow ("additional") page on the company's domain must be about —
# the same terms that define the priority slots ('stock' alone would match products)
ADDITIONAL_TOPICS = [kw for cat in ('about', 'community', 'news', 'investor', 'landing_pages')
                     for kw in get_category_keywords()[cat] if kw != 'stock']

# Overflow ("additional") links: skip pages that are about a place, a person or a
# product rather than the company — office locations, lawyer bios, contact pages,
# law-firm insights and practices, store/shopping pages
ADDITIONAL_EXCLUDE = re.compile(
    r'contact|/locations?/|/offices?/|/people/|/professionals?/|/lawyers?/|/practices?/|/insights?\b'
    r'|new arrivals|new releases|/shop|/store|/browse|/product|/gp/|log ?in|sign ?in', re.I)
SLOT_URL_EXCLUDE_DOCS = re.compile(r'\.pdf\b', re.I)  # about/community: a PDF is rarely the page itself


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _is_social_url(url: str) -> bool:
    domain = _extract_domain(url)
    return any(s in domain for s in SOCIAL_DOMAINS)


def _is_youtube_url(url: str) -> bool:
    domain = _extract_domain(url)
    return 'youtube.com' in domain or 'youtu.be' in domain


def _on_company_domain(url: str, company_domain: str) -> bool:
    if not company_domain:
        return False
    return company_domain in url


def _is_home_page(url: str, company_domain: str) -> bool:
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        return len(path) < 10 and '/' not in path
    except Exception:
        return False


def _company_name_in_title(title: str, company_name: str) -> bool:
    if not title or not company_name:
        return False
    title_lower = title.lower()
    company_lower = company_name.lower()
    if company_lower in title_lower:
        return True
    company_words = [w for w in company_lower.split() if len(w) > 2]
    if len(company_words) > 1:
        return company_words[0] in title_lower
    return False


def _matches_any_keyword(text: str, keywords: list) -> bool:
    """Verify a candidate is actually on-topic for its category, not just on-domain
    with the company name somewhere in the title (e.g. a generic 'About Google'
    page shouldn't win the 'leadership' slot just because it's on about.google)."""
    if not text or not keywords:
        return False
    text_lower = text.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        if len(kw) <= 4 or kw.isupper():
            # Short acronyms (CTO, CFO, CEO, CSR...) need word-boundary matching —
            # a plain substring check would match "CTO" inside "seCTOr", "CFO"
            # inside "comFOrt", etc.
            if re.search(r'(?<![a-z0-9])' + re.escape(kw_lower) + r'(?![a-z0-9])', text_lower):
                return True
        elif kw_lower in text_lower:
            return True
    return False


def _account_handle(url: str) -> str:
    """
    The account name in a social or YouTube profile URL — facebook.com/<h>,
    linkedin.com/company/<h>, tiktok.com/@<h>, youtube.com/@<h> /user/<h> /c/<h> —
    lowercased with punctuation and trailing digits removed. '' if there is none
    (e.g. an opaque youtube.com/channel/UC... id).
    """
    try:
        parts = [p for p in urlparse(url).path.split('/') if p]
    except Exception:
        return ''
    if not parts:
        return ''
    first = parts[0].lower()
    if first == 'channel':
        return ''
    if first in ('company', 'user', 'c', 'school', 'showcase') and len(parts) > 1:
        first = parts[1].lower()
    return re.sub(r'\d+$', '', re.sub(r'[^a-z0-9]', '', first))


def _company_handle_in_url(url: str, company_name: str, title: str = '') -> bool:
    """
    The profile's own handle is the company — the name, optionally plus a
    corporate suffix (@WalmartCorporate, kirkland-&-ellis-llp). Merely
    *containing* the name isn't enough: koch-media, walmart-connect and
    booz-&-company are other companies sharing a word.
    """
    handle = _account_handle(url)
    if not handle or not company_name:
        return False
    # The bare first word with nothing added (instagram.com/delta) — but only when the
    # profile itself names the company in full ("Delta Air Lines (@delta)"): @gibson is
    # Gibson Guitars, not Gibson Dunn
    words = _normalize(re.sub(r'^the\s+', '', company_name, flags=re.I)).split()
    if words and handle == words[0]:
        return len(words) == 1 or _company_name_strict(title, company_name)
    for form in _strict_name_forms(company_name):
        base = form.replace(' ', '')
        if handle.startswith(base) and handle[len(base):] in HANDLE_SUFFIXES:
            return True
    return False


def _company_channel_name(title: str, company_name: str) -> bool:
    """The YouTube channel is named the company ("Mars, Incorporated - YouTube"),
    not something that merely contains it ("Michael Cargill", "RTX Clan")."""
    name = _normalize(re.sub(r'\s*[-|]\s*youtube\s*$', '', title or '', flags=re.I))
    return CHANNEL_NAME_SUFFIX.sub('', name) in _strict_name_forms(company_name)


def _passes_slot_filters(category: str, url: str, title: str) -> bool:
    pattern = SLOT_TITLE_MUST_MATCH.get(category)
    if pattern and not pattern.search(title):
        return False
    if category in ('about', 'community', 'investor') and SLOT_URL_EXCLUDE.search(url):
        return False
    if category in ('about', 'community') and SLOT_URL_EXCLUDE_DOCS.search(url):
        return False
    return True


async def select_top_link_per_category(search_results: dict, company_name: str = None, company_domain: str = None, job_title: str = None) -> dict:
    """
    Select the best official-source link per category. Slots with no
    qualifying result are omitted.
    """
    categorized = {}
    category_keywords = get_category_keywords(job_title)

    for category, links in search_results.items():
        # 'youtube' still needs to run with an empty list so it can fall back
        # to an alternate social profile below.
        if not links and category != 'youtube':
            logger.info(f"[{category}] No links found, skipping")
            continue

        selected_link = None

        if category == 'home':
            for link in links:
                url = link.get('url', '')
                if _on_company_domain(url, company_domain) and _is_home_page(url, company_domain):
                    selected_link = link.copy()
                    break
            if not selected_link:
                for link in links:
                    if _on_company_domain(link.get('url', ''), company_domain):
                        selected_link = link.copy()
                        break

        elif category == 'social':
            # Prefer the company's own "follow us" hub page (lists every channel);
            # fall back to a single verified social profile.
            keywords = category_keywords.get('social', [])
            for link in links:
                url = link.get('url', '')
                title = link.get('title', '')
                if (_on_company_domain(url, company_domain)
                        and _matches_any_keyword(f"{title} {url}", keywords)):
                    selected_link = link.copy()
                    break
            if not selected_link:
                for link in links:
                    url = link.get('url', '')
                    if _is_social_url(url) and _company_handle_in_url(url, company_name, link.get('title', '')):
                        selected_link = link.copy()
                        break

        elif category == 'youtube':
            # Require an actual channel URL (not a bare video result that merely
            # mentions the company in its title, which could be a fan/news upload).
            # A title claiming to be "official" isn't proof by itself — impersonator
            # channels do that too — so each candidate is verified (LLM + thumbnail
            # check, in the resolver) before it can fill the slot; a candidate that
            # fails verification is skipped in favor of the next one, rather than
            # left in place as a wrong result.
            # Channels whose handle is the company (@Cargill) are tried before those whose
            # display name is (UC... ids have no handle) — names are easier to squat.
            channels = [l for l in links if _is_youtube_url(l.get('url', ''))
                        and parse_channel_url(l.get('url', '')) is not None]
            handle_match = [l for l in channels if _company_handle_in_url(l['url'], company_name, l.get('title', ''))]
            candidates = handle_match + [l for l in channels if l not in handle_match
                                         and _company_channel_name(l.get('title', ''), company_name)]
            for link in candidates:
                resolved = await resolve_youtube_channel_to_video(link.copy(), company_name=company_name)
                if resolved is None:
                    logger.info(f"[youtube] Candidate rejected, trying next: {link.get('title', '')[:60]}")
                    continue
                selected_link = resolved
                selected_link['type'] = 'video'
                break

            if not selected_link:
                # No official channel found — don't waste the slot, fall back to
                # another verified social profile (distinct from the one already
                # chosen for the 'social' slot, processed earlier in this loop).
                primary_social_url = categorized.get('social', {}).get('url')
                for social_link in search_results.get('social', []):
                    social_url = social_link.get('url', '')
                    if (social_url and social_url != primary_social_url
                            and _is_social_url(social_url)
                            and _company_handle_in_url(social_url, company_name, social_link.get('title', ''))):
                        selected_link = social_link.copy()
                        selected_link['category'] = 'Official Social Media'
                        break

        elif category in ('about', 'community', 'news', 'investor', 'role_specific', 'landing_pages'):
            # Require the topical keyword in the TITLE specifically — a curated,
            # reliable signal — rather than the description, which is free-form
            # marketing copy that can namedrop a topic without the page actually
            # being about it (e.g. an enterprise product page mentioning "board of
            # directors" while pitching to customers, not describing Google's own).
            keywords = category_keywords.get(category, [])
            for link in links:
                url = link.get('url', '')
                title = link.get('title', '')
                if (_on_company_domain(url, company_domain) and _company_name_in_title(title, company_name)
                        and _matches_any_keyword(title, keywords)
                        and _passes_slot_filters(category, url, title)):
                    selected_link = link.copy()
                    break

        if not selected_link:
            logger.info(f"[{category}] No qualifying link found, skipping")
            continue

        selected_link.setdefault('category', format_category_name(category))
        selected_link['category_key'] = category
        categorized[category] = selected_link
        logger.info(f"[{category}] Selected: {selected_link.get('title', '')[:60]}")

    return categorized


def order_by_priority(categorized_links: dict) -> list:
    """Return links in strict display order, omitting missing slots."""
    return [categorized_links[cat] for cat in PRIORITY_ORDER if cat in categorized_links]


def select_additional_links(
    search_results: dict,
    categorized_links: dict,
    company_name: str = None,
    company_domain: str = None,
    max_links: int = 5
) -> list:
    """
    Fill remaining room with leftover official-source links only: a page on the
    company domain that's about the company (careers, history, newsroom...), or a
    verified social profile — never a generic third-party result. Draws on the
    'landing_pages' results (careers, benefits, history, podcast, expansions)
    among others.
    """
    if max_links <= 0:
        return []

    seen_urls = {link.get('url') for link in categorized_links.values() if link.get('url')}
    additional = []

    for category, links in search_results.items():
        for link in links:
            if len(additional) >= max_links:
                return additional

            url = link.get('url', '')
            if not url or url in seen_urls:
                continue

            title = link.get('title', '')
            # An on-domain page must also be *about the company* (careers, history,
            # newsroom...) — otherwise any office, product or legal page qualifies
            on_domain_topic = (_on_company_domain(url, company_domain)
                               and _matches_any_keyword(title, ADDITIONAL_TOPICS))
            # (No YouTube here: a video can't be verified as official, and the YouTube
            # slot already shows the official channel.)
            is_official = (
                on_domain_topic or
                (_is_social_url(url) and _company_handle_in_url(url, company_name, title))
            )
            if (not is_official or ADDITIONAL_EXCLUDE.search(f"{title} {url}")
                    or SLOT_URL_EXCLUDE.search(url)):
                continue

            seen_urls.add(url)
            extra = link.copy()
            extra['category'] = 'Additional Links'
            extra['category_key'] = 'additional'
            additional.append(extra)

    return additional


async def _demo():
    """Self-check: priority order + skip-missing behaviour. Run: python -m app.utils.company_link_selection"""
    company, domain = "Delta Air Lines", "delta.com"
    results = {
        'home': [{'url': 'https://www.delta.com/', 'title': 'Delta Air Lines'}],
        'about': [{'url': 'https://www.delta.com/us/en/about-delta/overview',
                   'title': 'About Delta - Our Mission'}],
        'social': [{'url': 'https://www.delta.com/us/en/about-delta/follow-us',
                    'title': 'Follow Delta on Social Media'}],
        'youtube': [{'url': 'https://www.youtube.com/@delta', 'title': 'Delta Air Lines - YouTube'}],
        'community': [],  # no qualifying link -> slot skipped
        'news': [{'url': 'https://news.delta.com/', 'title': 'Delta News Hub - Newsroom'}],
        'investor': [{'url': 'https://ir.delta.com/', 'title': 'Delta Air Lines Investor Relations'}],
        'role_specific': [],
    }
    # No YOUTUBE_API_KEY/OPENAI_API_KEY in this bare script run, so the resolver
    # can't attempt verification — it hands the channel candidate back unchanged,
    # same as today's graceful degradation.
    categorized = await select_top_link_per_category(results, company_name=company, company_domain=domain)
    ordered = [l['category_key'] for l in order_by_priority(categorized)]
    assert ordered == ['home', 'about', 'social', 'youtube', 'news', 'investor'], ordered
    assert categorized['youtube']['type'] == 'video'
    print("ok:", ordered)

    # No official YouTube channel -> falls back to another verified social profile
    results_no_yt = {**results, 'youtube': [], 'social': [
        {'url': 'https://www.delta.com/us/en/about-delta/follow-us', 'title': 'Follow Delta on Social Media'},
        {'url': 'https://www.instagram.com/delta', 'title': 'Delta Air Lines (@delta) - Instagram'},
    ]}
    categorized_no_yt = await select_top_link_per_category(results_no_yt, company_name=company, company_domain=domain)
    assert categorized_no_yt['youtube']['url'] == 'https://www.instagram.com/delta'
    assert categorized_no_yt['youtube']['category'] == 'Official Social Media'
    assert 'type' not in categorized_no_yt['youtube']
    print("ok: youtube falls back to alt social profile")

    # An account is the company's only if its handle IS the company (plus a corporate
    # suffix at most) — not if it merely contains a word of the name
    assert _company_handle_in_url('https://www.youtube.com/@RTXCorporation', 'RTX')
    assert _company_handle_in_url('https://www.linkedin.com/company/kirkland-&-ellis-llp', 'Kirkland & Ellis')
    assert not _company_handle_in_url('https://linkedin.com/company/koch-media-', 'Koch')
    assert not _company_handle_in_url('https://www.youtube.com/@michaeldcargill', 'Cargill')
    assert _company_channel_name('Mars, Incorporated - YouTube', 'Mars')
    assert not _company_channel_name('RTX Clan - YouTube', 'RTX')
    print("ok: social/YouTube accounts must be the company, not share a word with it")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_demo())
