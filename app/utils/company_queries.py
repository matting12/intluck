"""
Query builders for company overview information (box 2).
Direct links from official company sources only — up to 8 links in strict
priority order (slots dropped if no qualifying result found):
1. Company Website
2. About Us / Company Overview
3. Mission, Vision & Culture
4. Community Engagement / Partnerships / Social Responsibility
5. Official Social Media (LinkedIn, X/Twitter, Instagram, Facebook, TikTok)
6. Leadership / Executive Team
7. Executive Content (videos, podcasts, investor recordings)
8. Role-Specific Page (department page for the job title, or the exec who owns it)

CATEGORY_KEYWORDS is the single source of truth for each category's topical
terms — used both to build the search query *and* (by company_link_selection)
to verify a candidate result is actually on-topic, not just on-domain with the
company name somewhere in the title.
"""

from app.utils.exact_match_companies import format_company_for_search
from app.utils.job_family import infer_job_family

__all__ = [
    'build_company_overview_queries',
    'format_category_name',
    'get_category_keywords'
]

CATEGORY_KEYWORDS = {
    'about': ['about us', 'who we are', 'our story', 'overview'],
    'mission_culture': ['our mission', 'our vision', 'company culture', 'our values', 'our goals', 'mission', 'vision', 'culture'],
    'community': ['community', 'foundation', 'giving back', 'corporate responsibility', 'social impact', 'csr', 'partnerships', 'partnership'],
    'leadership': ['leadership team', 'executive team', 'our leaders', 'meet the team', 'c-suite', 'board of directors', 'management team', 'leadership', 'executives'],
    'executive_content': ['ceo', 'cfo', 'executive', 'leadership', 'investor day', 'annual meeting', 'earnings', 'podcast', 'interview', 'investor'],
}

# Maps a job family (see app.utils.job_family) to the department the role
# belongs to and the C-suite executive who typically owns that department —
# used so we can still surface an official, role-relevant page even when a
# company has no dedicated department landing page.
ROLE_DEPARTMENT_MAP = {
    "Technology & Engineering": {"dept_terms": ["engineering team", "our engineers", "engineering careers", "product development team"], "executives": ["Chief Technology Officer", "CTO"]},
    "Finance & Accounting": {"dept_terms": ["finance team", "accounting team", "treasury team"], "executives": ["Chief Financial Officer", "CFO"]},
    "Healthcare & Medical": {"dept_terms": ["clinical team", "medical affairs", "patient care team"], "executives": ["Chief Medical Officer", "CMO"]},
    "Sales & Marketing": {"dept_terms": ["sales team", "marketing team"], "executives": ["Chief Marketing Officer", "Chief Revenue Officer"]},
    "Operations & Supply Chain": {"dept_terms": ["operations team", "supply chain team", "logistics team"], "executives": ["Chief Operating Officer", "COO"]},
    "Legal": {"dept_terms": ["legal team", "compliance team"], "executives": ["General Counsel", "Chief Legal Officer"]},
    "Human Resources": {"dept_terms": ["human resources team", "people team", "talent team"], "executives": ["Chief People Officer", "Chief Human Resources Officer"]},
    "Customer Service & Support": {"dept_terms": ["customer service team", "customer support team", "customer experience team"], "executives": ["Chief Customer Officer"]},
    "Data & Analytics": {"dept_terms": ["data team", "analytics team"], "executives": ["Chief Data Officer", "Chief Analytics Officer"]},
    "Product Management": {"dept_terms": ["product management team", "product team"], "executives": ["Chief Product Officer", "CPO"]},
    "Design & Creative": {"dept_terms": ["design team", "creative team"], "executives": ["Chief Design Officer", "Creative Director"]},
    "Education & Training": {"dept_terms": ["learning and development", "training team", "education team"], "executives": ["Chief Learning Officer"]},
    "Consulting": {"dept_terms": ["consulting team", "advisory team"], "executives": ["Managing Partner"]},
    "Retail & Hospitality": {"dept_terms": ["retail team", "store operations"], "executives": ["Chief Retail Officer"]},
    "Manufacturing & Engineering": {"dept_terms": ["manufacturing team", "production team"], "executives": ["Chief Operating Officer"]},
    "Research & Science": {"dept_terms": ["research team", "R&D team", "science team"], "executives": ["Chief Scientific Officer", "Chief Research Officer"]},
    "Real Estate & Property": {"dept_terms": ["real estate team", "property team"], "executives": ["Chief Real Estate Officer"]},
    "Media & Entertainment": {"dept_terms": ["media team", "content team", "production team"], "executives": ["Chief Content Officer"]},
    "Non-Profit & Government": {"dept_terms": ["community programs", "public affairs team"], "executives": ["Chief Program Officer"]},
    "Transportation & Logistics": {"dept_terms": ["transportation team", "logistics team", "fleet team"], "executives": ["Chief Logistics Officer"]},
    "General": {"dept_terms": ["our team", "careers"], "executives": ["Chief Executive Officer", "CEO"]},
}


def format_category_name(category_key: str) -> str:
    category_names = {
        'home': 'Company Website',
        'about': 'About Us',
        'mission_culture': 'Mission, Vision & Culture',
        'community': 'Community Engagement',
        'social': 'Official Social Media',
        'leadership': 'Leadership & Executive Team',
        'executive_content': 'Executive Content',
        'role_specific': 'Role-Specific Page',
        'additional': 'Additional Links',
    }
    return category_names.get(category_key, category_key.replace('_', ' ').title())


def _role_specific_terms(job_title: str = None) -> list:
    """Department + executive terms relevant to a job title's job family."""
    family = infer_job_family(job_title) if job_title else "General"
    role_info = ROLE_DEPARTMENT_MAP.get(family, ROLE_DEPARTMENT_MAP["General"])
    return role_info["dept_terms"] + role_info["executives"]


def get_category_keywords(job_title: str = None) -> dict:
    """
    Topical keywords per category, used to verify a candidate result is
    actually on-topic (not just on-domain with the company name in the title).
    Includes the job-title-derived terms for 'role_specific'.
    """
    keywords = {**CATEGORY_KEYWORDS}
    keywords['role_specific'] = _role_specific_terms(job_title)
    return keywords


def _or_query(terms: list) -> str:
    return ' OR '.join(f'"{t}"' if ' ' in t else t for t in terms)


def build_company_overview_queries(
    company: str,
    company_domain: str,
    job_title: str = None,
    location: str = None,
) -> dict:
    """
    Build queries for company overview — direct links from official company
    sources only. Every query is restricted to the company's own domain,
    except 'social' (official social profiles) and 'executive_content'
    (official YouTube channel / podcast appearances / investor recordings).

    Returns: {category_key: search_query_string}
    """
    c = format_company_for_search(company)

    role_terms = _role_specific_terms(job_title)

    queries = {
        # 1. Company Website
        'home': f'{c} site:{company_domain}',

        # 2. About Us / Company Overview
        'about': f'{c} ({_or_query(CATEGORY_KEYWORDS["about"])}) site:{company_domain}',

        # 3. Mission, Vision & Culture
        'mission_culture': f'{c} ({_or_query(CATEGORY_KEYWORDS["mission_culture"])}) site:{company_domain}',

        # 4. Community Engagement / Partnerships / Social Responsibility
        'community': f'{c} ({_or_query(CATEGORY_KEYWORDS["community"])}) site:{company_domain}',

        # 5. Official Social Media
        'social': f'{c} official (site:facebook.com OR site:instagram.com OR site:x.com OR site:tiktok.com OR site:linkedin.com/company)',

        # 6. Leadership / Executive Team
        'leadership': f'{c} ({_or_query(CATEGORY_KEYWORDS["leadership"])}) site:{company_domain}',

        # 7. Executive Content — videos, podcasts, investor recordings (official channel/site only)
        'executive_content': f'{c} ({_or_query(CATEGORY_KEYWORDS["executive_content"])}) (site:youtube.com/watch OR site:spotify.com OR site:podcasts.apple.com OR site:{company_domain})',

        # 8. Role-Specific Page — department page for the job title, falling back to the exec who owns it
        'role_specific': f'{c} ({_or_query(role_terms)}) (team OR division OR department OR leadership OR "meet our") site:{company_domain}',
    }

    return queries
