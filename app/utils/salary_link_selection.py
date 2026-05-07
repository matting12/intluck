"""
Link selection and ordering for salary & benefits.
Similar to company_link_selection but for compensation data.
"""

__all__ = [
    'select_top_salary_link_per_category',
    'order_salary_by_priority'
]

import logging
import re
from urllib.parse import urlparse
from app.utils.salary_queries import format_salary_category_name

logger = logging.getLogger(__name__)

# Trusted domains that get a pass on title matching
TRUSTED_PASS_DOMAINS = {
    'glassdoor.com', 'levels.fyi', 'linkedin.com', 'indeed.com',
    'payscale.com', 'salary.com', 'comparably.com', 'blind.com',
    'teamblind.com', 'reddit.com', 'leetcode.com', 'github.com',
    'vault.com', 'fishbowlapp.com', 'careerbliss.com'
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
    """Check if company name appears in the title as a whole word (not as a substring of another word)."""
    if not title or not company_name:
        return False

    title_lower = title.lower()
    company_lower = company_name.lower()

    # Word-boundary match: "adp" must not be immediately followed by a letter/digit
    # Prevents "ADP" matching inside "ADPI", "ADPList", etc.
    pattern = re.escape(company_lower) + r'(?![a-zA-Z0-9])'
    if re.search(pattern, title_lower):
        return True

    # For multi-word names, check the first significant word with same boundary rule
    company_words = [w for w in company_lower.split() if len(w) > 2]
    if len(company_words) > 1:
        word_pattern = re.escape(company_words[0]) + r'(?![a-zA-Z0-9])'
        return bool(re.search(word_pattern, title_lower))

    return False


def _company_name_in_url(url: str, company_name: str) -> bool:
    """Check if company name appears as a path segment in the URL (not just a substring)."""
    if not url or not company_name:
        return False
    try:
        from urllib.parse import urlparse
        path = urlparse(url).path.lower()
        name = company_name.lower().replace(' ', '').replace('&', '').replace('.', '')
        segments = [s for s in path.replace('-', '/').split('/') if s]
        return name in segments
    except Exception:
        return False


def _should_include_link(link: dict, company_name: str) -> bool:
    """Check if link belongs to the right company — name must appear in title or URL path."""
    if _company_name_in_title(link.get('title', ''), company_name):
        return True
    if _company_name_in_url(link.get('url', ''), company_name):
        return True
    return False


def select_top_salary_link_per_category(search_results: dict, company_name: str = None) -> dict:
    """
    For each category, select the top Brave search result.

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
            filtered_links = links

            # Filter by company name in title OR trusted domain
            if company_name:
                filtered_links = [
                    link for link in links
                    if _should_include_link(link, company_name)
                ]
                if filtered_links:
                    logger.info(f"[{category}] Filtered to {len(filtered_links)} relevant links")
                else:
                    logger.info(f"[{category}] No relevant links found, skipping category")
                    continue  # Skip this category entirely

            # Take first result from Brave
            top_link = filtered_links[0].copy()

            # Add formatted category name
            top_link['category'] = format_salary_category_name(category)
            top_link['category_key'] = category

            categorized[category] = top_link

    return categorized


def order_salary_by_priority(categorized_links: dict) -> list:
    """
    Return links in spec-defined priority order.
    
    Priority order from spec:
    1. Benefits landing page
    2. Perks
    3. ERG groups
    4. Salary
    5. Equity/Stock
    6. Health insurance reviews
    7. Insurance cost
    8. Retirement/401K
    9. Pay increases
    10. Benefits comparison
    """
    
    priority_order = [
        'benefits_landing',
        'perks',
        'erg_groups',
        'salary',
        'equity',
        'health_insurance',
        'insurance_cost',
        'retirement_401k',
        'pay_increases',
        'benefits_comparison'
    ]
    
    ordered = []
    for category in priority_order:
        if category in categorized_links:
            ordered.append(categorized_links[category])
    
    return ordered