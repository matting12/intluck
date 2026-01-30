"""
Link selection and ordering for company overview.
Replaces GPT selection with category-based approach.
"""

__all__ = [
    'select_top_link_per_category',
    'order_by_priority'
]

import logging
from urllib.parse import urlparse
from app.utils.company_queries import format_category_name

logger = logging.getLogger(__name__)

# Trusted domains that get a pass on title matching
TRUSTED_PASS_DOMAINS = {
    'glassdoor.com', 'levels.fyi', 'linkedin.com', 'indeed.com',
    'payscale.com', 'salary.com', 'comparably.com', 'blind.com',
    'teamblind.com', 'reddit.com', 'leetcode.com', 'github.com',
    'vault.com', 'fishbowlapp.com', 'careerbliss.com', 'youtube.com'
}


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


def _is_trusted_domain(url: str) -> bool:
    """Check if URL is from a trusted domain that gets a pass on title matching."""
    domain = _extract_domain(url)
    for trusted in TRUSTED_PASS_DOMAINS:
        if domain == trusted or domain.endswith('.' + trusted):
            return True
    return False


def _company_name_in_title(title: str, company_name: str) -> bool:
    """
    Check if company name appears in the title.
    Handles multi-word company names by checking if all significant words appear.
    """
    if not title or not company_name:
        return False

    title_lower = title.lower()
    company_lower = company_name.lower()

    # Direct match first
    if company_lower in title_lower:
        return True

    # For multi-word names, check if the main words appear
    # e.g., "Bell Helicopter" -> check for "bell" AND "helicopter"
    company_words = [w for w in company_lower.split() if len(w) > 2]
    if len(company_words) > 1:
        # Require at least the first significant word (usually the brand name)
        return company_words[0] in title_lower

    return False


def _should_include_link(link: dict, company_name: str) -> bool:
    """Check if link should be included based on company name OR trusted domain."""
    # Always include if company name in title
    if _company_name_in_title(link.get('title', ''), company_name):
        return True

    # Also include if from a trusted domain
    if _is_trusted_domain(link.get('url', '')):
        return True

    return False


def select_top_link_per_category(search_results: dict, company_name: str = None) -> dict:
    """
    For each category, select the top Brave search result.
    No GPT needed - Brave ranking + site:{domain} filter provides quality.
    Videos are prioritized to appear first if present.

    If company_name is provided, filters to only links containing the company name in title.

    Args:
        search_results: {category: [list of link dicts]}
        company_name: Optional company name to filter by (must appear in title)

    Returns:
        {category: single_link_dict}
    """

    categorized = {}

    for category, links in search_results.items():
        if links and len(links) > 0:
            # Sort links so videos appear first
            sorted_links = sorted(links, key=lambda x: 0 if x.get('type') == 'video' else 1)

            # Filter by company name in title OR trusted domain
            if company_name:
                filtered_links = [
                    link for link in sorted_links
                    if _should_include_link(link, company_name)
                ]
                if filtered_links:
                    sorted_links = filtered_links
                    logger.info(f"[{category}] Filtered to {len(filtered_links)} relevant links")
                else:
                    logger.info(f"[{category}] No relevant links found, skipping category")
                    continue  # Skip this category entirely

            # Take first result (will be video if one exists)
            top_link = sorted_links[0].copy()

            # Add formatted category name
            top_link['category'] = format_category_name(category)
            top_link['category_key'] = category

            categorized[category] = top_link

    return categorized


def order_by_priority(categorized_links: dict) -> list:
    """
    Return links in spec-defined priority order.
    
    Priority order from spec:
    1. About Us
    2. Mission/Vision Statement
    3. Company Culture
    4. Department/Leadership
    5. Social Media
    6. History
    7. Community Engagement
    8. Financial Reports
    9. News
    """
    
    priority_order = [
        'about_us',
        'mission_vision',
        'culture',
        'department',
        'social_media',
        'history',
        'community',
        'financials',
        'news'
    ]
    
    ordered = []
    for category in priority_order:
        if category in categorized_links:
            ordered.append(categorized_links[category])
    
    return ordered