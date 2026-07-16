"""
Link selection and ordering for company overview (box 2).
Direct links from official company sources only — selects up to 8 links in
strict priority order:
1. Company Website          (home)
2. About Us                 (about)
3. Mission, Vision & Culture (mission_culture)
4. Community Engagement     (community)
5. Official Social Media    (social)
6. Leadership & Executives  (leadership)
7. Executive Content        (executive_content) — videos, podcasts, investor recordings
8. Role-Specific Page       (role_specific) — department page, or the exec who owns it

Every slot is restricted to the company's own domain, except 'social'
(official social profiles) and 'executive_content' (official YouTube channel /
podcast appearances / investor recordings, which don't live on the company
domain but are still directly produced by the company).

Slots are dropped if no qualifying link is found — no fillers.
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

# Official channels/platforms companies publish executive content to directly
EXEC_CONTENT_DOMAINS = {'youtube.com', 'youtu.be', 'spotify.com', 'podcasts.apple.com'}

PRIORITY_ORDER = ['home', 'about', 'mission_culture', 'community', 'social', 'leadership', 'executive_content', 'role_specific']

# Categories official-only sources are drawn from for the "additional links" catch-all
OFFICIAL_DOMAIN_CATEGORIES = {'home', 'about', 'mission_culture', 'community', 'leadership', 'role_specific'}


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


def _is_exec_content_url(url: str) -> bool:
    domain = _extract_domain(url)
    return any(d in domain for d in EXEC_CONTENT_DOMAINS)


def _is_youtube_url(url: str) -> bool:
    domain = _extract_domain(url)
    return 'youtube.com' in domain or 'youtu.be' in domain


def _is_youtube_channel(url: str) -> bool:
    return any(p in url for p in ['/channel/', '/c/', '/@', '/user/'])


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
            for link in links:
                url = link.get('url', '')
                if _is_social_url(url) and _company_handle_in_url(url, company_name):
                    selected_link = link.copy()
                    break

        elif category in ('about', 'mission_culture', 'community', 'leadership', 'role_specific'):
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

        elif category == 'executive_content':
            keywords = category_keywords.get('executive_content', [])
            candidates = [
                link for link in links
                if (_is_exec_content_url(link.get('url', '')) or _on_company_domain(link.get('url', ''), company_domain))
                and _company_name_in_title(link.get('title', ''), company_name)
                and _matches_any_keyword(link.get('title', ''), keywords)
            ]
            # Prefer an actual YouTube watch URL (embeddable) over a channel page
            watch_hits = [l for l in candidates if not (_is_youtube_url(l.get('url', '')) and _is_youtube_channel(l.get('url', '')))]
            chosen = watch_hits[0] if watch_hits else (candidates[0] if candidates else None)
            if chosen:
                selected_link = chosen.copy()
                if _is_youtube_url(selected_link.get('url', '')):
                    selected_link['type'] = 'video'

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
    company domain, an official social profile, or executive content (official
    YouTube/podcast/investor recording) — never a generic third-party result.
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
                (_is_exec_content_url(url) and _company_name_in_title(title, company_name))
            )
            if not is_official:
                continue

            seen_urls.add(url)
            extra = link.copy()
            extra['category'] = 'Additional Links'
            extra['category_key'] = 'additional'
            additional.append(extra)

    return additional
