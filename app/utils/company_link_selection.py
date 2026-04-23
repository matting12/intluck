"""
Link selection and ordering for company overview.
Selects exactly 5 links in order:
1. Home page
2. About Us
3. Social Media
4. Company History
5. YouTube video

No fallback - if a category has no results, it's skipped.
"""

__all__ = [
    'select_top_link_per_category',
    'order_by_priority'
]

import logging
from urllib.parse import urlparse
from app.utils.company_queries import format_category_name

logger = logging.getLogger(__name__)


def _extract_domain(url: str) -> str:
    """Extract base domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube link."""
    domain = _extract_domain(url)
    return 'youtube.com' in domain or 'youtu.be' in domain


def _is_home_page(url: str, company_domain: str) -> bool:
    """Check if URL is likely a home page (short path)."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        # Home page typically has no path or very short path
        return len(path) < 10 and '/' not in path
    except Exception:
        return False


def _company_name_in_title(title: str, company_name: str) -> bool:
    """
    Check if company name appears in the title.
    """
    if not title or not company_name:
        return False

    title_lower = title.lower()
    company_lower = company_name.lower()

    # Direct match first
    if company_lower in title_lower:
        return True

    # For multi-word names, check if the first significant word appears
    company_words = [w for w in company_lower.split() if len(w) > 2]
    if len(company_words) > 1:
        return company_words[0] in title_lower

    return False


def select_top_link_per_category(search_results: dict, company_name: str = None, company_domain: str = None) -> dict:
    """
    For each category, select the best matching link.
    No fallback - if category has no valid results, it's excluded.

    Args:
        search_results: {category: [list of link dicts]}
        company_name: Company name to filter by (must appear in title for most categories)
        company_domain: Company domain for home page detection

    Returns:
        {category: single_link_dict}
    """

    categorized = {}

    for category, links in search_results.items():
        if not links or len(links) == 0:
            logger.info(f"[{category}] No links found, skipping")
            continue

        selected_link = None

        # For YouTube, find a video from the official channel
        if category == 'youtube':
            for link in links:
                url = link.get('url', '')
                title = link.get('title', '')
                if _is_youtube_url(url) and _company_name_in_title(title, company_name):
                    selected_link = link.copy()
                    selected_link['type'] = 'video'
                    break
            if not selected_link:
                logger.info(f"[{category}] No official YouTube video found, skipping")
                continue

        # For home page, prefer shortest URL path on company domain
        elif category == 'home':
            for link in links:
                url = link.get('url', '')
                if company_domain and company_domain in url:
                    if _is_home_page(url, company_domain):
                        selected_link = link.copy()
                        break
            # If no short path found, take first link on company domain
            if not selected_link:
                for link in links:
                    url = link.get('url', '')
                    if company_domain and company_domain in url:
                        selected_link = link.copy()
                        break
            if not selected_link:
                logger.info(f"[{category}] No home page found, skipping")
                continue

        # For other categories, require company name in title
        else:
            for link in links:
                title = link.get('title', '')
                if _company_name_in_title(title, company_name):
                    selected_link = link.copy()
                    break

            if not selected_link:
                logger.info(f"[{category}] No relevant link found (company name not in title), skipping")
                continue

        # Add formatted category name
        selected_link['category'] = format_category_name(category)
        selected_link['category_key'] = category
        categorized[category] = selected_link
        logger.info(f"[{category}] Selected: {selected_link.get('title', 'No title')[:50]}")

    return categorized


def order_by_priority(categorized_links: dict) -> list:
    """
    Return links in the specified order:
    1. Home Page
    2. About Us
    3. Social Media
    4. Company History
    5. YouTube Video
    """

    priority_order = [
        'home',
        'about',
        'social',
        'history',
        'youtube'
    ]

    ordered = []
    for category in priority_order:
        if category in categorized_links:
            ordered.append(categorized_links[category])

    return ordered
