"""
Query builders for salary and benefits information (company overview box 3).
Generates queries for up to 6 links in strict priority order, plus a
"remaining" catch-all of extra benefits/perks reviews:
1. Company Website - Benefits/Total Rewards/Perks (benefits_landing)
2-4. Job title + salary + company name             (salary — top 3 distinct-domain hits)
5. Company name medical benefits and perks          (medical_benefits)
6. Reviews on benefits and perks - company name     (benefits_reviews)
Remaining: more benefits/perks reviews, drawn from leftover medical_benefits /
benefits_reviews results.
"""

from app.utils.exact_match_companies import format_company_for_search

__all__ = [
    'build_salary_benefits_queries',
    'format_salary_category_name'
]

# Preferred sites for salary lookups
SALARY_SITES = '(site:glassdoor.com OR site:indeed.com OR site:levels.fyi OR site:payscale.com OR site:salary.com OR site:ambitionbox.com OR site:comparably.com OR site:blind.com OR site:h1bdata.info OR site:bls.gov)'

# Preferred sites for benefits/perks reviews
REVIEW_SITES = '(site:glassdoor.com OR site:indeed.com OR site:comparably.com OR site:ambitionbox.com OR site:blind.com OR site:fishbowlapp.com OR site:greatplacetowork.com OR site:vault.com OR site:reddit.com)'


def format_salary_category_name(category_key: str) -> str:
    """Convert category_key to display name"""
    category_names = {
        'benefits_landing': 'Company Benefits & Total Rewards',
        'salary': 'Salary Information',
        'medical_benefits': 'Medical Benefits & Perks',
        'benefits_reviews': 'Benefits & Perks Reviews',
        'additional': 'More Benefits Reviews',
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def build_salary_benefits_queries(
    company: str,
    company_domain: str,
    job_title: str,
    location: str,
    state: str = ""
) -> dict:
    """
    Build category-specific queries for salary & benefits overview.

    The 'salary' query returns a ranked list of results from our preferred salary
    sites — the caller takes the top 3 distinct-domain hits to fill slots 2-4.

    Returns: {category_key: search_query_string}
    """
    c = format_company_for_search(company)
    location_part = f'{location}' if location and location != 'REMOTE' else ''

    queries = {
        # 1. Company Website - Benefits/Total Rewards/Perks
        'benefits_landing': f'{c} (benefits OR "total rewards" OR perks OR "benefits package") site:{company_domain}',

        # 2-4. Job title + salary + company name (preferred salary sites; top 3 distinct results used)
        'salary': f'{c} {job_title} {location_part} (salary OR "pay rate" OR "total compensation package" OR compensation) {SALARY_SITES} -jobs -hiring -"job posting" -careers -apply',

        # 5. Company name medical benefits and perks
        'medical_benefits': f'{c} ("medical benefits" OR "health benefits" OR "healthcare benefits" OR perks) (reviews OR overview OR breakdown) {REVIEW_SITES}',

        # 6. Reviews on benefits and perks - company name
        'benefits_reviews': f'{c} ("employee reviews" OR reviews OR rating OR feedback) ("benefits" OR "perks" OR "total rewards") {REVIEW_SITES}',
    }

    return queries
