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

logger = logging.getLogger(__name__)

SOCIAL_DOMAINS = {'facebook.com', 'instagram.com', 'x.com', 'twitter.com', 'tiktok.com', 'linkedin.com'}

PRIORITY_ORDER = ['home', 'about', 'social', 'youtube', 'community', 'news', 'investor', 'role_specific']


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


def _company_handle_in_url(url: str, company_name: str) -> bool:
    """
    Check the social profile's own handle/path segment for an exact match to the
    company name — much stronger evidence of an official account than the page
    title, which can collide with unrelated people/pages sharing a short or
    common company name (e.g. "Baird" matching a person named "Noah Baird").
    """
    if not url or not company_name:
        return False
    try:
        path = urlparse(url).path.lower()
        name = company_name.lower().replace(' ', '').replace('&', '').replace('.', '')
        segments = [s for s in path.replace('-', '/').split('/') if s]
        if name in segments:
            return True
        company_words = [w for w in company_name.lower().split() if len(w) > 2]
        if len(company_words) > 1 and company_words[0] in segments:
            return True
        return False
    except Exception:
        return False


def select_top_link_per_category(search_results: dict, company_name: str = None, company_domain: str = None, job_title: str = None) -> dict:
    """
    Select the best official-source link per category. Slots with no
    qualifying result are omitted.
    """
    categorized = {}
    category_keywords = get_category_keywords(job_title)

    for category, links in search_results.items():
        if not links:
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
                    if _is_social_url(url) and _company_handle_in_url(url, company_name):
                        selected_link = link.copy()
                        break

        elif category == 'youtube':
            for link in links:
                url = link.get('url', '')
                if _is_youtube_url(url) and _company_name_in_title(link.get('title', ''), company_name):
                    selected_link = link.copy()
                    selected_link['type'] = 'video'  # resolved to featured video downstream
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
                        and _matches_any_keyword(title, keywords)):
                    selected_link = link.copy()
                    break

        if not selected_link:
            logger.info(f"[{category}] No qualifying link found, skipping")
            continue

        selected_link['category'] = format_category_name(category)
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
    Fill remaining room with leftover official-source links only: on the
    company domain, a verified social profile, or the official YouTube channel
    — never a generic third-party result. Draws on the 'landing_pages' results
    (careers, benefits, history, podcast, expansions) among others.
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
            is_official = (
                _on_company_domain(url, company_domain) or
                (_is_social_url(url) and _company_handle_in_url(url, company_name)) or
                (_is_youtube_url(url) and _company_name_in_title(title, company_name))
            )
            if not is_official:
                continue

            seen_urls.add(url)
            extra = link.copy()
            extra['category'] = 'Additional Links'
            extra['category_key'] = 'additional'
            additional.append(extra)

    return additional


def _demo():
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
    categorized = select_top_link_per_category(results, company_name=company, company_domain=domain)
    ordered = [l['category_key'] for l in order_by_priority(categorized)]
    assert ordered == ['home', 'about', 'social', 'youtube', 'news', 'investor'], ordered
    assert categorized['youtube']['type'] == 'video'
    print("ok:", ordered)


if __name__ == "__main__":
    _demo()
