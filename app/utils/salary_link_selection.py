"""
Link selection and ordering for salary & benefits (company overview box 3).
Selects up to 6 links in strict priority order:
1. Company Website - Benefits/Total Rewards/Perks (benefits_landing)
2. Salary Information                              (salary_1)
3. Salary Information                              (salary_2)
4. Salary Information                              (salary_3)
5. Medical Benefits & Perks                        (medical_benefits)
6. Benefits & Perks Reviews                        (benefits_reviews)

Slots are dropped if no qualifying link is found — no fillers. Remaining room
(up to a caller-supplied cap) is filled with extra benefits/perks reviews via
select_additional_salary_links.
"""

__all__ = [
    'select_top_salary_link_per_category',
    'order_salary_by_priority',
    'select_additional_salary_links'
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
    'vault.com', 'fishbowlapp.com', 'careerbliss.com', 'greatplacetowork.com',
    'ambitionbox.com', 'bls.gov', 'h1bdata.info'
}

PRIORITY_ORDER = ['benefits_landing', 'salary_1', 'salary_2', 'salary_3', 'medical_benefits', 'benefits_reviews']

# Categories the "remaining links" catch-all draws from — review-focused only
REVIEW_CATEGORIES = ['medical_benefits', 'benefits_reviews']


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
    For each non-salary category, select the top Brave search result.
    For 'salary', select up to 3 distinct-domain results to fill slots
    salary_1/salary_2/salary_3.

    If company_name is provided, filters to only links containing the company
    name in title or URL (or a trusted domain, for salary results).

    Args:
        search_results: {category: [list of link dicts]}
        company_name: Optional company name to filter by

    Returns:
        {category_key: single_link_dict} — category_key is 'salary_1'/'salary_2'/'salary_3'
        for the salary bucket, otherwise the category name itself.
    """

    categorized = {}

    for category, links in search_results.items():
        if not links:
            continue

        filtered_links = links
        if company_name:
            filtered_links = [
                link for link in links
                if _should_include_link(link, company_name) or (category == 'salary' and _is_trusted_domain(link.get('url', '')))
            ]
            if not filtered_links:
                logger.info(f"[{category}] No relevant links found, skipping category")
                continue
            logger.info(f"[{category}] Filtered to {len(filtered_links)} relevant links")

        if category == 'salary':
            seen_domains = set()
            slot_num = 1
            for link in filtered_links:
                if slot_num > 3:
                    break
                domain = _extract_domain(link.get('url', ''))
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)
                slot_key = f'salary_{slot_num}'
                entry = link.copy()
                entry['category'] = format_salary_category_name('salary')
                entry['category_key'] = slot_key
                categorized[slot_key] = entry
                slot_num += 1
            continue

        top_link = filtered_links[0].copy()
        top_link['category'] = format_salary_category_name(category)
        top_link['category_key'] = category
        categorized[category] = top_link

    return categorized


def order_salary_by_priority(categorized_links: dict) -> list:
    """Return links in strict display order, omitting missing slots."""
    return [categorized_links[cat] for cat in PRIORITY_ORDER if cat in categorized_links]


def select_additional_salary_links(
    search_results: dict,
    categorized_links: dict,
    company_name: str = None,
    max_links: int = 5
) -> list:
    """
    Remaining slots: leftover benefits/perks review links not already used in a
    priority slot, drawn only from the review-focused search buckets
    (medical_benefits, benefits_reviews) — i.e. "reviews on benefits".
    """
    if max_links <= 0:
        return []

    seen_urls = {link.get('url') for link in categorized_links.values() if link.get('url')}
    additional = []

    for category in REVIEW_CATEGORIES:
        for link in search_results.get(category, []):
            if len(additional) >= max_links:
                return additional

            url = link.get('url', '')
            if not url or url in seen_urls:
                continue

            if company_name and not _should_include_link(link, company_name):
                continue

            seen_urls.add(url)
            extra = link.copy()
            extra['category'] = format_salary_category_name('additional')
            extra['category_key'] = 'additional'
            additional.append(extra)

    return additional
