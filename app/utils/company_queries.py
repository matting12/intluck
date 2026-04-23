"""
Query builders for company overview information.
Generates queries for up to 5 links (slots dropped if no result found):
1. Company website (home page)
2. About Us / Who We Are
3. Social Media (Facebook/Instagram/X/TikTok)
4. Community Engagement (CSR/foundation/giving)
5. Video or Department Vertical (YouTube video preferred, dept page fallback)
"""

from app.utils.exact_match_companies import format_company_for_search

__all__ = [
    'build_company_overview_queries',
    'format_category_name'
]


def format_category_name(category_key: str) -> str:
    category_names = {
        'home': 'Company Website',
        'about': 'About Us',
        'social': 'Social Media',
        'community': 'Community Engagement',
        'video_or_vertical': 'Video',
        'video': 'Video',
        'dept_vertical': 'Department',
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def build_company_overview_queries(
    company: str,
    company_domain: str,
    job_title: str = None,
    location: str = None,
) -> dict:
    """
    Build queries for company overview. Returns 6 query keys — video and
    dept_vertical are both run and the winner becomes slot 5.

    Returns: {category_key: search_query_string}
    """
    company_formatted = format_company_for_search(company)

    queries = {
        # 1. Home page
        'home': f'{company_formatted} site:{company_domain}',

        # 2. About Us
        'about': f'{company_formatted} ("about us" OR "who we are" OR "about the company" OR "our company" OR "our story" OR "our mission" OR overview) site:{company_domain}',

        # 3. Social Media — official profiles on major platforms (no YouTube, no LinkedIn)
        'social': f'{company_formatted} (site:facebook.com OR site:instagram.com OR site:x.com OR site:tiktok.com)',

        # 4. Community Engagement — CSR/foundation/giving on company domain
        'community': f'{company_formatted} ("community" OR "foundation" OR "giving back" OR "corporate responsibility" OR "social impact" OR "CSR") site:{company_domain}',

        # 5a. Video — official YouTube channel page (web search surfaces channel pages better than video API)
        'video': f'{company_formatted} official channel site:youtube.com',

        # 5b. Department Vertical — careers/teams/divisions page on company domain
        'dept_vertical': f'{company_formatted} (careers OR "our teams" OR "our people" OR "research" OR "divisions" OR "departments") site:{company_domain}',
    }

    return queries
