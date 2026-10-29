"""
Query builders for salary and benefits information (company overview box 3).
Generates queries for up to 9 links in strict priority order:
1.   Company Website - Benefits/Total Rewards/Perks   (benefits_landing)
2-3. Salaries for job title at company                (salary)
4-5. Negotiating salary at company, falling back to
     negotiating salary for the job title             (negotiation_company, negotiation_role)
6-7. External reviews of company benefits & perks     (benefits_reviews, medical_benefits)
8.   Social media video on company benefits           (benefits_videos)
9.   Benefits comparison by industry                  (industry_comparison)
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

# Social platforms that host short company-benefits videos
VIDEO_SITES = '(site:youtube.com OR site:tiktok.com OR site:instagram.com OR site:linkedin.com)'

NOT_JOB_POSTINGS = '-jobs -hiring -"job posting" -careers -apply'


def format_salary_category_name(category_key: str) -> str:
    """Convert category_key to display name"""
    category_names = {
        'benefits_landing': 'Company Benefits & Total Rewards',
        'salary': 'Salary Information',
        'negotiation': 'Negotiating Salary',
        'benefits_reviews': 'Benefits & Perks Reviews',
        'benefits_videos': 'Benefits Video',
        'industry_comparison': 'Industry Benefits Comparison',
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def build_salary_benefits_queries(
    company: str,
    company_domain: str,
    job_title: str,
    location: str,
    state: str = "",
    industry: str = ""
) -> dict:
    """
    Build category-specific queries for salary & benefits overview.
    Returns: {category_key: search_query_string}
    """
    c = format_company_for_search(company)
    location_part = f'{location}' if location and location != 'REMOTE' else ''
    # Unknown industry -> compare against the company's own industry/competitors
    industry_part = f'"{industry}" industry' if industry else f'{c} (industry OR competitors)'

    return {
        # 1. Company Website - Benefits/Total Rewards/Perks
        'benefits_landing': f'{c} (benefits OR "total rewards" OR perks OR "benefits package") site:{company_domain}',

        # 2-3. Job title + salary + company name
        'salary': f'{c} {job_title} {location_part} (salary OR "pay rate" OR "total compensation package" OR compensation) {SALARY_SITES} {NOT_JOB_POSTINGS}',

        # 4-5. Negotiating salary — company first, job title as fallback
        'negotiation_company': f'{c} (negotiate OR negotiating OR negotiation) (salary OR offer OR compensation) {NOT_JOB_POSTINGS}',
        'negotiation_role': f'"{job_title}" (negotiate OR negotiating OR negotiation) (salary OR offer) {NOT_JOB_POSTINGS}',

        # 6-7. External reviews on company benefits and perks
        'benefits_reviews': f'{c} ("employee reviews" OR reviews OR rating OR feedback) ("benefits" OR "perks" OR "total rewards") {REVIEW_SITES}',
        'medical_benefits': f'{c} ("medical benefits" OR "health benefits" OR "healthcare benefits" OR perks) (reviews OR overview OR breakdown) {REVIEW_SITES}',

        # 8. Social media video on company benefits
        'benefits_videos': f'{c} ("employee benefits" OR "employee perks" OR "working at" OR "total rewards") {VIDEO_SITES}',

        # 9. Benefits comparison based on industry
        'industry_comparison': f'{industry_part} ("employee benefits" OR perks) (comparison OR benchmark OR "compared to" OR average)',
    }
