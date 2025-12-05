"""
Query builders for company overview information.
Generates category-specific search queries restricted to company domain.
"""

from app.utils.job_family import infer_job_family

__all__ = [
    'build_company_overview_queries',
    'build_department_query',
    'build_social_media_query',
    'is_zipcode',
    'format_category_name'
]


def is_zipcode(location: str) -> bool:
    """Check if location is a 5-digit zipcode"""
    return location.isdigit() and len(location) == 5


from app.utils.zipcode_to_city import zipcode_to_city

async def get_state_from_zipcode(zipcode: str) -> str:
    """Extract state from zipcode using existing utility"""
    city_state = await zipcode_to_city(zipcode)
    
    if ',' in city_state:
        return city_state.split(',')[1].strip()
    
    return city_state


def format_category_name(category_key: str) -> str:
    """Convert category_key to display name"""
    category_names = {
        'about_us': 'About Us',
        'mission_vision': 'Mission & Vision',
        'culture': 'Company Culture',
        'department': 'Department & Leadership',
        'social_media': 'Social Media',
        'history': 'Company History',
        'community': 'Community Engagement',
        'financials': 'Financial Reports',
        'news': 'Recent News'
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def build_department_query(company: str, domain: str, job_title: str, job_family: str) -> str:
    """
    Build department/leadership query with 4 strategy variations.
    
    Strategy 1: Direct job title match
    Strategy 2: Job family department
    Strategy 3: Job family with scope/overview keywords
    Strategy 4: Leadership team pages
    """
    
    variations = [
        f'"{job_title}" (team OR group OR department OR "leadership team")',
        f'{job_family} department',
        f'{job_family} (team OR department OR group) AND (scope OR inside OR look OR overview)',
        f'{job_family} ("leadership team" OR "executive leadership")'
    ]
    
    # Combine with OR
    combined = " OR ".join(f"({v})" for v in variations)
    
    return f'{company} ({combined}) site:{domain}'


def build_social_media_query(company: str, domain: str) -> str:
    """Search for links to social media on company site"""
    return f'{company} (LinkedIn OR Facebook OR Instagram OR TikTok OR YouTube OR podcast) site:{domain}'


def build_company_overview_queries(
    company: str,
    company_domain: str,
    job_title: str,
    location: str,
) -> dict:
    """
    Build 9 category-specific queries for company overview.
    All queries restricted to company domain only.
    
    Returns: {category_name: search_query_string}
    """
    
    
    # Infer job family from title
    job_family = infer_job_family(job_title)
    
    queries = {
        'about_us': f'{company} ("about us") site:{company_domain}',
        
        'mission_vision': f'{company} ("mission statement" OR "vision statement") site:{company_domain} language:en',
        
        'culture': f'{company} ("company culture" OR "company values" OR "corporate culture" OR "organization culture" OR DEI OR "work environment") site:{company_domain}',
        
        'department': build_department_query(company, company_domain, job_title, job_family),
        
        'social_media': build_social_media_query(company, company_domain),
        
        'history': f'{company} (history OR growth) site:{company_domain}',
        
        'community': f'{company} ("community engagement" OR "community involvement" OR "giving back") site:{company_domain}',
        
        'financials': f'{company} ("financial reports" OR "quarterly reports" OR "stock reports") site:{company_domain}',
        
        'news': f'{company} (news OR updates) site:{company_domain}'
    }
    
    return queries