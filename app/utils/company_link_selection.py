"""
Link selection and ordering for company overview.
Selects up to 5 links in strict order:
1. Company Website
2. About Us
3. Social Media
4. Community Engagement
5. Video or Department Vertical

Slots are dropped if no qualifying link is found — no fillers.
"""

__all__ = [
    'select_top_link_per_category',
    'order_by_priority'
]

import logging
from urllib.parse import urlparse
from app.utils.company_queries import format_category_name

logger = logging.getLogger(__name__)

SOCIAL_DOMAINS = {'facebook.com', 'instagram.com', 'x.com', 'twitter.com', 'tiktok.com'}

PRIORITY_ORDER = ['home', 'about', 'social', 'community', 'video_or_vertical']


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _is_youtube_url(url: str) -> bool:
    domain = _extract_domain(url)
    return 'youtube.com' in domain or 'youtu.be' in domain


def _is_social_url(url: str) -> bool:
    domain = _extract_domain(url)
    return any(s in domain for s in SOCIAL_DOMAINS)


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


def select_top_link_per_category(search_results: dict, company_name: str = None, company_domain: str = None) -> dict:
    """
    Select the best link per category. Slots with no qualifying result are omitted.
    video and dept_vertical results are merged into a single video_or_vertical slot.
    """
    categorized = {}

    for category, links in search_results.items():
        # video and dept_vertical handled together below
        if category in ('video', 'dept_vertical'):
            continue

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
                title = link.get('title', '')
                if _is_social_url(url) and _company_name_in_title(title, company_name):
                    selected_link = link.copy()
                    break

        elif category in ('about', 'community'):
            for link in links:
                url = link.get('url', '')
                title = link.get('title', '')
                if _on_company_domain(url, company_domain) and _company_name_in_title(title, company_name):
                    selected_link = link.copy()
                    break

        else:
            for link in links:
                if _company_name_in_title(link.get('title', ''), company_name):
                    selected_link = link.copy()
                    break

        if not selected_link:
            logger.info(f"[{category}] No qualifying link found, skipping")
            continue

        selected_link['category'] = format_category_name(category)
        selected_link['category_key'] = category
        categorized[category] = selected_link
        logger.info(f"[{category}] Selected: {selected_link.get('title', '')[:60]}")

    # Slot 5: try video first, fall back to dept page, pick best
    video_link = None
    dept_link = None

    def _is_youtube_channel(url: str) -> bool:
        return any(p in url for p in ['/channel/', '/c/', '/@', '/user/'])

    video_candidates = [
        l for l in search_results.get('video', [])
        if _is_youtube_url(l.get('url', '')) and _company_name_in_title(l.get('title', ''), company_name)
    ]
    # Prefer official channel pages over watch URLs
    channel_hits = [l for l in video_candidates if _is_youtube_channel(l.get('url', ''))]
    if channel_hits:
        video_link = channel_hits[0].copy()
        video_link['type'] = 'video'
    elif video_candidates:
        video_link = video_candidates[0].copy()
        video_link['type'] = 'video'

    for link in search_results.get('dept_vertical', []):
        url = link.get('url', '')
        title = link.get('title', '')
        if _on_company_domain(url, company_domain) and _company_name_in_title(title, company_name):
            dept_link = link.copy()
            break

    # Prefer video; fall back to dept page
    winner = video_link if video_link else dept_link
    if winner:
        winner['category'] = 'Video' if winner is video_link else 'Department'
        winner['category_key'] = 'video_or_vertical'
        categorized['video_or_vertical'] = winner
        logger.info(f"[video_or_vertical] Selected ({'video' if winner is video_link else 'dept'}): {winner.get('title', '')[:60]}")
    else:
        logger.info("[video_or_vertical] No qualifying link found, skipping")

    return categorized


def order_by_priority(categorized_links: dict) -> list:
    """Return links in strict display order, omitting missing slots."""
    return [categorized_links[cat] for cat in PRIORITY_ORDER if cat in categorized_links]
