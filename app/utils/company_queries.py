"""
Query builders for company overview information.
Generates specific queries for exactly 5 links:
1. Company home page
2. About Us / Who We Are
3. Social Media
4. Company History
5. YouTube (official channel video)
"""

from app.utils.exact_match_companies import format_company_for_search

__all__ = [
    'build_company_overview_queries',
    'format_category_name'
]


def format_category_name(category_key: str) -> str:
    """Convert category_key to display name"""
    category_names = {
        'home': 'Home Page',
        'about': 'About Us',
        'social': 'Social Media',
        'history': 'Company History',
        'youtube': 'Video'
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def build_company_overview_queries(
    company: str,
    company_domain: str,
    job_title: str = None,
    location: str = None,
) -> dict:
    """
    Build 5 specific queries for company overview.
    Each query targets exactly one type of page.

    Returns: {category_name: search_query_string}
    """

    # Format company name (exact match if needed)
    company_formatted = format_company_for_search(company)

    queries = {
        # 1. Home page - just the company domain
        'home': f'{company_formatted} site:{company_domain}',

        # 2. About Us / Who We Are page
        'about': f'{company_formatted} ("about us" OR "who we are" OR "about the company") site:{company_domain}',

        # 3. Social Media page (links to social platforms)
        'social': f'{company_formatted} (LinkedIn OR Facebook OR Instagram OR Twitter OR TikTok) site:{company_domain}',

        # 4. Company History
        'history': f'{company_formatted} ("our history" OR "company history" OR "our story" OR "founded" OR "since") site:{company_domain}',

        # 5. YouTube - official company channel video
        'youtube': f'{company_formatted} official site:youtube.com'
    }

    return queries
