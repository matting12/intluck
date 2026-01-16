"""
Query builders for salary and benefits information.
Generates category-specific search queries with fallback strategies.
"""

from app.utils.job_family import infer_job_family
from app.utils.exact_match_companies import format_company_for_search

__all__ = [
    'build_salary_benefits_queries',
    'build_salary_fallback_query',
    'format_salary_category_name'
]


def format_salary_category_name(category_key: str) -> str:
    """Convert category_key to display name"""
    category_names = {
        'benefits_landing': 'Benefits Overview',
        'perks': 'Company Perks',
        'erg_groups': 'Employee Resource Groups',
        'salary': 'Salary Information',
        'equity': 'Stock & Equity',
        'health_insurance': 'Health Insurance Reviews',
        'insurance_cost': 'Insurance Cost Reviews',
        'retirement_401k': 'Retirement & 401K',
        'pay_increases': 'Pay Increases & Raises',
        'benefits_comparison': 'Benefits Comparison'
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def build_salary_fallback_query(company: str, job_title: str, location: str, state: str) -> str:
    """
    Build salary query with location fallback strategy.

    Strategy:
    1. Try with specific location (city or zipcode)
    2. If no results, backend can retry with state only
    3. If still no results, backend can retry with no location

    For now, we build the most specific query and let Brave handle relevance.
    """
    company_formatted = format_company_for_search(company)

    base = f'{company_formatted} {job_title}'
    location_part = f'{location}' if location and location != 'REMOTE' else ''
    salary_terms = '(salary OR "pay rate" OR "total compensation package" OR compensation)'

    # Preferred salary sites
    sites = '(site:glassdoor.com OR site:indeed.com OR site:levels.fyi OR site:payscale.com OR site:salary.com OR site:ambitionbox.com OR site:comparably.com OR site:blind.com OR site:h1bdata.info OR site:bls.gov)'

    # Exclude job postings
    exclusions = '-jobs -hiring -"job posting" -careers -apply'

    query_parts = [base, location_part, salary_terms, sites, exclusions]
    return ' '.join(part for part in query_parts if part).strip()


def build_salary_benefits_queries(
    company: str,
    company_domain: str,
    job_title: str,
    location: str,
    state: str = ""
) -> dict:
    """
    Build 10 category-specific queries for salary & benefits.
    All queries follow spec with proper boolean search syntax.
    Uses exact matching for companies with common words in their names.

    Args:
        company: Company name
        company_domain: Company's main domain
        job_title: Job title
        location: Location (city/state format or "REMOTE")
        state: State only (for fallback queries)

    Returns:
        {category_name: search_query_string}
    """
    # Format company name (exact match if needed)
    c = format_company_for_search(company)

    queries = {
        # 1. Benefits landing page on company site
        'benefits_landing': f'{c} (benefits OR retirement OR insurance OR "total rewards" OR healthcare OR perks) site:{company_domain}',

        # 2. Perks working at company
        'perks': f'{c} (perks OR "show appreciation to employees" OR "pros of working for {company}" OR "why working for {company} is" (fun OR great OR awesome))',

        # 3. ERG groups
        'erg_groups': f'{c} (ERG OR "employee resource groups") site:{company_domain}',

        # 4. Salary information (with fallback strategy)
        'salary': build_salary_fallback_query(company, job_title, location, state),

        # 5. Stock/RSU/Equity
        'equity': f'{c} {job_title} (stock OR RSU OR vesting OR bonus OR equity) (site:levels.fyi OR site:ambitionbox.com OR site:fishbowlapp.com OR site:glassdoor.com OR site:reddit.com OR site:youtube.com OR site:{company_domain})',

        # 6. Health insurance reviews
        'health_insurance': f'{c} ("employee reviews" OR reviews OR ranking OR rating OR feedback) ("health insurance" OR "medical insurance" OR "healthcare benefits" OR "total rewards") AND ("life insurance" OR "life coverage") (site:glassdoor.com OR site:indeed.com OR site:ambitionbox.com OR site:blind.com OR site:levels.fyi OR site:reddit.com OR site:fishbowlapp.com OR site:greatplacetowork.com OR site:vault.com)',

        # 7. Health insurance cost reviews
        'insurance_cost': f'{c} (costs OR price OR premium OR rates) ("employee reviews" OR reviews OR ranking OR rating) ("health insurance" OR "medical insurance" OR "healthcare benefits" OR "healthcare cost" OR "benefits breakdown") (site:glassdoor.com OR site:indeed.com OR site:ambitionbox.com OR site:blind.com OR site:levels.fyi OR site:reddit.com OR site:fishbowlapp.com OR site:h1bdata.info)',

        # 8. 401K/Retirement reviews
        'retirement_401k': f'{c} ("employee reviews" OR reviews OR ranking OR rating OR feedback OR experiences) (401K OR 401b OR "retirement options" OR "retirement plan" OR "retirement benefits" OR retirement OR pension OR saving OR "matching contribution") (site:glassdoor.com OR site:indeed.com OR site:ambitionbox.com OR site:blind.com OR site:levels.fyi OR site:reddit.com OR site:fishbowlapp.com OR site:h1bdata.info)',

        # 9. Annual pay increases
        'pay_increases': f'{c} ("annual pay increase" OR "annual raise" OR "salary increase" OR "salary raise" OR "pay adjustment" OR "merit increase" OR "wage increase" OR "performance reviews" OR "cost of living") ("employee reviews" OR reviews OR ranking OR rating OR feedback OR experiences) (site:glassdoor.com OR site:indeed.com OR site:ambitionbox.com OR site:blind.com OR site:levels.fyi OR site:reddit.com OR site:fishbowlapp.com OR site:h1bdata.info)',

        # 10. Benefits comparison
        'benefits_comparison': f'{c} ("benefits package" OR "employee benefits" OR "compensation package" OR "health benefits" OR "retirement benefits") AND ("compare" OR "comparison" OR "market standards" OR "industry standards" OR "competitive" OR "value")'
    }

    return queries