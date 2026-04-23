"""
Job family-specific query templates for company-specific interview prep.
Each family has queries designed to find company tools, processes, and real interview data.
"""

from app.utils.exact_match_companies import format_company_for_search

def get_interview_prep_queries(company: str, job_title: str, job_family: str) -> list[str]:
    """
    Generate 4-5 targeted queries based on job family.
    Focus on: company-specific interview experiences, actual interview questions, role insights,
    and LinkedIn "how I became" inspiration posts.

    Args:
        company: Company name (e.g., "Microsoft", "Burlington")
        job_title: Job title (e.g., "Software Engineer", "Accountant")
        job_family: Job family category (e.g., "Technology & Engineering")

    Returns:
        List of 4-5 search query strings optimized for that job family
    """
    # Format company name with exact matching if needed
    c = format_company_for_search(company)

    # LinkedIn inspiration query - common to all job families
    linkedin_query = f'{c} ("how I became" OR "my journey to" OR "how I got my job" OR "landed a job") {job_title} site:linkedin.com'

    query_templates = {
        "Technology & Engineering": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:levels.fyi OR site:leetcode.com',
            f'{c} {job_title} interview experience site:reddit.com OR site:blind.com',
            f'{c} engineering blog OR tech stack OR architecture',
            f'{c} {job_title} "what to expect" OR "interview process"',
            linkedin_query
        ],

        "Finance & Accounting": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com OR site:wallstreetoasis.com',
            f'{c} finance OR accounting "interview process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Healthcare & Medical": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} healthcare "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Sales & Marketing": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com OR site:repvue.com',
            f'{c} marketing OR sales "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Operations & Supply Chain": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} operations "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Legal": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:vault.com',
            f'{c} {job_title} interview experience site:reddit.com OR site:abovethelaw.com',
            f'{c} legal "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Human Resources": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} HR "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Customer Service & Support": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} customer service "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Data & Analytics": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:levels.fyi',
            f'{c} {job_title} interview experience site:reddit.com OR site:blind.com',
            f'{c} data science OR analytics "interview process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Product Management": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:levels.fyi',
            f'{c} {job_title} interview experience site:reddit.com OR site:blind.com',
            f'{c} product manager "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Design & Creative": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} design "interview process" OR "portfolio review"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Education & Training": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} education "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Consulting": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:vault.com',
            f'{c} {job_title} interview experience site:reddit.com OR site:managementconsulted.com',
            f'{c} consulting "case interview" OR "interview process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Retail & Hospitality": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} retail OR hospitality "interview process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Manufacturing & Engineering": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} manufacturing "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Research & Science": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} research "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Real Estate & Property": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} real estate "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Media & Entertainment": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} media "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Non-Profit & Government": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} government OR nonprofit "interview process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ],

        "Transportation & Logistics": [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} logistics "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ]
    }
    
    # Get queries for this job family, or fall back to generic
    if job_family in query_templates:
        return query_templates[job_family]
    else:
        # Generic fallback for unknown job families
        return [
            f'{c} {job_title} interview questions site:glassdoor.com OR site:indeed.com',
            f'{c} {job_title} interview experience site:reddit.com',
            f'{c} {job_title} "interview process" OR "hiring process"',
            f'{c} {job_title} "what to expect" OR "how to prepare"',
            linkedin_query
        ]


def get_company_info_queries(company: str) -> list[str]:
    """
    Generate queries for company information section.
    Focus on: official company sources, leadership, culture, social presence
    """
    return [
        f"{company} about OR company overview site:linkedin.com OR site:crunchbase.com",
        f"{company} leadership OR executives OR management team",
        f"{company} culture OR values OR mission OR careers",
        f"{company} news OR press releases OR announcements"
    ]


def get_salary_queries(company: str, job_title: str, location: str) -> list[str]:
    """
    Generate queries for salary and benefits section.
    Focus on: compensation data, benefits, work-life balance
    
    Args:
        location: City, State format (e.g., "Seattle, WA")
    """
    return [
        f"{company} {job_title} salary {location} site:levels.fyi OR site:glassdoor.com",
        f"{company} {job_title} compensation site:levels.fyi OR site:payscale.com",
        f"{company} benefits OR perks OR employee benefits",
        f"{company} work life balance OR remote work OR flexible schedule"
    ]


def get_reviews_queries(company: str) -> list[str]:
    """
    Generate queries for company reviews section.
    Focus on: employee reviews, culture insights, career development
    """
    return [
        f"{company} employee reviews site:glassdoor.com OR site:indeed.com OR site:comparably.com",
        f"{company} culture OR workplace OR employee experience",
        f"{company} career development OR growth opportunities OR promotions",
        f"{company} management OR leadership reviews"
    ]