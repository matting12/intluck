from fastapi import APIRouter, HTTPException
import logging
import asyncio
import httpx
import json
import time
import logging


from app.services.domain_identifier import identify_company_domain
from app.services.brave_search import brave_search
from app.models.company_info import CompanyInfoResult
from app.utils.link_formatting import format_link_for_display
from app.utils.trusted_domains import filter_to_trusted_domains, filter_blacklisted, deduplicate_by_domain
from app.utils import *
from app.utils.company_queries import build_company_overview_queries
from app.utils.company_link_selection import select_top_link_per_category, order_by_priority
from app.utils.domain_overrides import get_domain_override
from app.utils.salary_queries import build_salary_benefits_queries
from app.utils.salary_link_selection import select_top_salary_link_per_category, order_salary_by_priority


import os

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



router = APIRouter()
logger = logging.getLogger(__name__)


async def select_best_links_with_gpt(
    company: str,
    all_links: list[dict],
    OPENAI_API_KEY: str,
    max_links: int = 5
) -> list[dict]:
    """
    Use gpt-3.5-turbo to select the most relevant company information links.
    """
    
    if not all_links:
        return []
    
    prompt = f"""You are analyzing search results about {company} to find the most valuable links for someone researching the company.

Select the {max_links} MOST RELEVANT links. Prioritize:
1. Official "About Us" pages with mission/values
2. Company culture and values pages  
3. Main company LinkedIn profile (not individual employee profiles)
4. Executive leadership pages or CEO content
5. Company overview/history pages
6. Main Instagram/Twitter accounts (not regional or individual)

AVOID:
- Individual job postings (but company careers page is OK)
- Specific location/store pages
- Technical documentation or PDFs
- Press releases about specific products
- Individual employee LinkedIn profiles
- Blog posts unless they're about company mission/values

Available links:
{json.dumps(all_links, indent=2)}

YOU MUST RESPOND WITH ONLY VALID JSON. NO MARKDOWN. NO CODE BLOCKS. NO EXPLANATIONS.

Return a JSON array with exactly {max_links} objects:
[
  {{
    "url": "full URL",
    "title": "page title",
    "description": "description",
    "category": "About & Mission" | "Culture & Values" | "Leadership" | "Social Media" | "Company Overview"
  }}
]"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a research assistant. You ONLY respond with valid JSON arrays. Never use markdown code blocks."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Strip markdown if present (some models ignore instructions)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            selected_links = json.loads(content)
            
            # Validate structure
            if isinstance(selected_links, list) and len(selected_links) > 0:
                return selected_links[:max_links]
            else:
                logger.warning("Invalid GPT response structure, using fallback")
                return fallback_selection(all_links, max_links)
                
    except Exception as e:
        logger.error(f"GPT selection error: {e}")
        return fallback_selection(all_links, max_links)


async def select_salary_links_with_gpt(
    company: str,
    job_title: str,
    all_links: list[dict],
    OPENAI_API_KEY: str,
    max_links: int = 5
) -> list[dict]:
    """
    Use gpt-3.5-turbo to select the most relevant salary and benefits links.
    Customized for compensation data from aggregator sites.
    """
    
    if not all_links:
        return []
    
    prompt = f"""You are analyzing search results about {company} compensation and benefits for a {job_title} role.

Select the {max_links} MOST RELEVANT links. Prioritize:
1. Glassdoor, Levels.fyi, Payscale, Indeed, Built In - salary aggregators
2. Links with SPECIFIC NUMBERS: salary ranges, 401k match %, PTO days, equity details
3. Employee reviews mentioning compensation and benefits
4. Company benefits pages with detailed package information

AVOID:
- Job postings (they say "competitive salary" but no real data)
- News articles unless they have specific compensation data
- Generic "how to negotiate salary" articles
- Links without concrete salary or benefits information

Available links:
{json.dumps(all_links, indent=2)}

YOU MUST RESPOND WITH ONLY VALID JSON. NO MARKDOWN. NO CODE BLOCKS. NO EXPLANATIONS.

Return a JSON array with exactly {max_links} objects:
[
  {{
    "url": "full URL",
    "title": "page title",
    "description": "description",
    "category": "Salary Data" | "Benefits & Perks" | "Employee Reviews" | "Compensation Overview"
  }}
]"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a compensation research assistant. You ONLY respond with valid JSON arrays. Never use markdown code blocks."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Strip markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            selected_links = json.loads(content)
            
            if isinstance(selected_links, list) and len(selected_links) > 0:
                return selected_links[:max_links]
            else:
                logger.warning("Invalid GPT response structure, using fallback")
                return fallback_selection(all_links, max_links)
                
    except Exception as e:
        logger.error(f"GPT selection error for salary/benefits: {e}")
        return fallback_selection(all_links, max_links)


async def select_review_links_with_gpt(
    company: str,
    all_links: list[dict],
    OPENAI_API_KEY: str,
    max_links: int = 6
) -> list[dict]:
    """
    Use gpt-3.5-turbo to select 6 company review links (2 per category).
    """
    
    if not all_links:
        return []
    
    prompt = f"""You are analyzing search results about {company} to find insights on company news, culture, and career development.

Select {max_links} links - EXACTLY 2 FROM EACH CATEGORY:

**Company News & Updates (2 links):**
- Recent news & earnings reports
- Financial performance, growth initiatives
- Executive changes, mergers, acquisitions
- Prioritize 2023-2025 content

**Culture & Work Environment (2 links):**
- Employee reviews about culture and values
- Work-life balance, remote work policies
- Team dynamics, diversity initiatives
- What makes this company unique

**Career Development (2 links):**
- Promotion paths and career progression
- Training programs, tuition reimbursement
- Mentorship and professional development
- Employee growth opportunities

Prioritize:
1. Glassdoor, Comparably, Blind, Indeed, LinkedIn for culture/career
2. Recent content (2023-2025) for news
3. Employee perspectives over company press releases
4. Specific examples and data over generic statements

AVOID:
- Company press releases (too biased)
- Individual job postings
- Old news (pre-2023)
- Generic articles without specific insights

Available links:
{json.dumps(all_links, indent=2)}

YOU MUST RESPOND WITH ONLY VALID JSON. NO MARKDOWN. NO CODE BLOCKS. NO EXPLANATIONS.

Return a JSON array with exactly {max_links} objects (2 per category):
[
  {{
    "url": "full URL",
    "title": "page title",
    "description": "description",
    "category": "Company News" | "Culture & Work Environment" | "Career Development"
  }}
]"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a company research assistant. You ONLY respond with valid JSON arrays. Never use markdown code blocks. Select EXACTLY 2 links per category."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Strip markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            selected_links = json.loads(content)
            
            if isinstance(selected_links, list) and len(selected_links) > 0:
                return selected_links[:max_links]
            else:
                logger.warning("Invalid GPT response structure, using fallback")
                return fallback_selection(all_links, max_links)
                
    except Exception as e:
        logger.error(f"GPT selection error for company reviews: {e}")
        return fallback_selection(all_links, max_links)


async def select_interview_prep_links_with_gpt(
    company: str,
    job_title: str,
    all_links: list[dict],
    OPENAI_API_KEY: str,
    max_links: int = 6
) -> list[dict]:
    """
    Use gpt-3.5-turbo to select interview prep links with priority order.
    """
    
    if not all_links:
        return []
    
    prompt = f"""You are analyzing search results to find interview preparation resources for a {job_title} role at {company}.

Select UP TO {max_links} links using this PRIORITY ORDER:

**Priority 1 (HIGHEST): Company-Specific Interview Questions**
- Actual interview questions asked at {company}
- Employee interview experiences from Glassdoor, Blind, Reddit
- {company}-specific interview process and format
- Real candidate stories and experiences

**Priority 2 (HIGH): Company Tech Stack & Tools**
- Technologies and tools used at {company}
- Programming languages, frameworks, platforms they use
- Company engineering blog posts about their stack
- Methodologies and processes specific to {company}

**Priority 3 (MEDIUM): Technical Skills for {job_title}**
- Core competencies needed for this role
- Technical knowledge areas to review
- Skills and concepts relevant to {job_title}

**Priority 4 (LOW - Use as filler only): Generic Interview Prep**
- General interview tips for {job_title} across companies
- Common behavioral questions
- General advice (only if nothing better available)

Prioritize:
1. Glassdoor interview sections and Blind posts (real experiences)
2. Company engineering blogs (official tech stack info)
3. Specific examples over generic advice
4. Recent content (2023-2025)

AVOID:
- Job postings
- Generic "10 interview tips" clickbait articles
- Content with no specific, actionable information
- Paywalled content that doesn't show preview info

IMPORTANT: Return 4-6 links. Quality over quantity - don't force links if good content isn't available.

Available links:
{json.dumps(all_links, indent=2)}

YOU MUST RESPOND WITH ONLY VALID JSON. NO MARKDOWN. NO CODE BLOCKS. NO EXPLANATIONS.

Return a JSON array with 4-6 objects:
[
  {{
    "url": "full URL",
    "title": "page title",
    "description": "description",
    "category": "Company Interview Questions" | "Tech Stack & Tools" | "Technical Skills" | "General Prep"
  }}
]"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an interview preparation research assistant. You ONLY respond with valid JSON arrays. Never use markdown code blocks. Prioritize quality over quantity."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Strip markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            selected_links = json.loads(content)
            
            if isinstance(selected_links, list) and len(selected_links) > 0:
                return selected_links[:max_links]
            else:
                logger.warning("Invalid GPT response structure, using fallback")
                return fallback_selection(all_links, max_links)
                
    except Exception as e:
        logger.error(f"GPT selection error for interview prep: {e}")
        return fallback_selection(all_links, max_links)


def fallback_selection(all_links: list[dict], max_links: int) -> list[dict]:
    """Simple rule-based fallback if GPT fails."""
    
    scored = []
    
    for link in all_links:
        url = link['url'].lower()
        title = link['title'].lower()
        
        # Skip obvious non-company-info links
        if any(bad in url for bad in ['job/', '/careers/job/', 'location/', '.pdf']):
            continue
        if 'linkedin.com/in/' in url:  # individual profile
            continue
            
        score = 0
        
        # Score based on keywords
        if any(kw in title or kw in url for kw in ['about', 'mission', 'overview']):
            score += 10
        if any(kw in title or kw in url for kw in ['culture', 'values', 'life at']):
            score += 9
        if 'leadership' in title or 'executive' in title:
            score += 8
        if 'linkedin.com/company/' in url:
            score += 7
        if 'careers' in url and 'job' not in url:
            score += 5
            
        scored.append((score, link))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    
    return [
        {
            **link,
            "category": "Company Information"
        }
        for _, link in scored[:max_links]
    ]


@router.get("/company-info", response_model=dict)
async def get_company_info(
    company: str,
    job_title: str,
    location: str,
    max_links: int = 9,
    no_cache: bool = False
):
    """
    Get curated company information links.
    Uses category-specific queries restricted to company domain.
    """
    start_time = time.time()

    cache_params = {
        'company': company.lower().strip(),
        'job_title': job_title.lower().strip(),
        'location': location.strip()
    }
    
    # Only check cache if no_cache is False
    if not no_cache:
        cached_result = get_cached('company_info', cache_params)
        if cached_result:
            elapsed = time.time() - start_time
            logger.info(f"Cache hit for company_info - returned in {elapsed:.2f}s")
            return cached_result
    else:
        logger.info(f"Cache disabled for this request")

    logger.info(f"Company info request: company='{company}', job_title='{job_title}', location='{location}'")

    # PASS 1: Identify company domain (with override check)
    domain_override = get_domain_override(company)
    
    if domain_override:
        domain = domain_override
        logger.info(f"Using domain override: {domain}")
    else:
        domain = await identify_company_domain(company, BRAVE_API_KEY)
        if not domain:
            return {
                "domain": None,
                "links": [],
                "error": "Could not identify company domain"
            }
        logger.info(f"Identified domain: {domain}")

    # PASS 2: Build category-specific queries
    queries = build_company_overview_queries(company, domain, job_title, location)
    logger.info(f"Built {len(queries)} category-specific queries")

    # PASS 3: Execute searches in parallel
    search_start = time.time()
    
    tasks = [
        brave_search(query, BRAVE_API_KEY, category)
        for category, query in queries.items()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    search_elapsed = time.time() - search_start
    logger.info(f"Brave searches took {search_elapsed:.2f}s")

    # PASS 4: Organize results by category
    search_results = {}
    for category, result_data in zip(queries.keys(), results_list):
        if isinstance(result_data, Exception):
            logger.error(f"Error in category '{category}': {result_data}")
            search_results[category] = []
        else:
            search_results[category] = result_data
    
    logger.info(f"Got results for {len([c for c, r in search_results.items() if r])} categories")

    # PASS 5: Select top link per category (no GPT needed)
    categorized_links = select_top_link_per_category(search_results)
    logger.info(f"Selected {len(categorized_links)} links (1 per category)")

    # PASS 6: Order by priority
    ordered_links = order_by_priority(categorized_links)

    # PASS 6.5: Deduplicate by URL
    seen_urls = set()
    deduped_links = []

    for link in ordered_links:
        url = link.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped_links.append(link)
        else:
            logger.info(f"Duplicate URL filtered: {url}")

    logger.info(f"After deduplication: {len(deduped_links)} links (removed {len(ordered_links) - len(deduped_links)} duplicates)")

    # PASS 7: Format titles for display
    formatted_links = [format_link_for_display(link) for link in deduped_links[:max_links]]

    result = {
        "domain": domain,
        "links": formatted_links,
        "total_found": len(categorized_links)
    }

    if not no_cache:
        set_cached('company_info', cache_params, result, ttl=SEVEN_DAYS)
    
    total_elapsed = time.time() - start_time
    logger.info(f"Total company_info took {total_elapsed:.2f}s (search: {search_elapsed:.2f}s)")
    
    return result


@router.get("/salary-benefits", response_model=dict)
async def get_salary_benefits(
    company: str,
    job_title: str,
    location: str = "REMOTE",
    max_links: int = 5,
    no_cache: bool = False
):
    """
    Get salary and benefits information.
    Uses category-specific queries with fallback strategies.
    """
    start_time = time.time()
    
    cache_params = {
        'company': company.lower().strip(),
        'job_title': job_title.lower().strip(),
        'location': location.strip()
    }
    
    if not no_cache:
        cached_result = get_cached('salary_benefits', cache_params)
        if cached_result:
            elapsed = time.time() - start_time
            logger.info(f"Cache hit for salary_benefits - returned in {elapsed:.2f}s")
            return cached_result
    else:
        logger.info("Cache disabled for this request")
    
    logger.info(f"Salary/benefits request: company='{company}', job_title='{job_title}', location='{location}'")
    
    # PASS 1: Get company domain (needed for site: searches)
    domain_override = get_domain_override(company)
    
    if domain_override:
        domain = domain_override
        logger.info(f"Using domain override: {domain}")
    else:
        domain = await identify_company_domain(company, BRAVE_API_KEY)
        if not domain:
            domain = f"{company.lower().replace(' ', '')}.com"
            logger.warning(f"Could not identify domain, using fallback: {domain}")
    
    # PASS 2: Handle location conversion
    if location == "REMOTE" or not location:
        city_state = "Remote"
        state = ""
        logger.info("Remote role - location set to 'Remote'")
    elif location:
        # Assume location is already in "City, State" format from frontend
        city_state = location
        # Extract state if in "City, ST" format
        if ',' in location:
            state = location.split(',')[1].strip()
        else:
            state = ""
        logger.info(f"Using location: {city_state}")
    
    # PASS 3: Build category-specific queries
    queries = build_salary_benefits_queries(company, domain, job_title, city_state, state)
    logger.info(f"Built {len(queries)} salary/benefits queries")
    
    # PASS 4: Execute searches in parallel
    search_start = time.time()
    
    tasks = [
        brave_search(query, BRAVE_API_KEY, category)
        for category, query in queries.items()
    ]
    
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    search_elapsed = time.time() - search_start
    logger.info(f"Brave searches took {search_elapsed:.2f}s")
    
    # PASS 5: Organize results by category
    search_results = {}
    for category, result_data in zip(queries.keys(), results_list):
        if isinstance(result_data, Exception):
            logger.error(f"Error in category '{category}': {result_data}")
            search_results[category] = []
        else:
            search_results[category] = result_data
    
    logger.info(f"Got results for {len([c for c, r in search_results.items() if r])} categories")
    
    # PASS 6: Select top link per category (no GPT needed)
    categorized_links = select_top_salary_link_per_category(search_results)
    logger.info(f"Selected {len(categorized_links)} links (1 per category)")
    
    # PASS 7: Order by priority
    ordered_links = order_salary_by_priority(categorized_links)
    
    # PASS 8: Deduplicate by URL
    seen_urls = set()
    deduped_links = []
    
    for link in ordered_links:
        url = link.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped_links.append(link)
        else:
            logger.info(f"Duplicate URL filtered: {url}")
    
    logger.info(f"After deduplication: {len(deduped_links)} links")
    
    # PASS 9: Format titles for display
    formatted_links = [format_link_for_display(link) for link in deduped_links[:max_links]]
    
    result = {
        "company": company,
        "job_title": job_title,
        "location": location,
        "links": formatted_links,
        "total_found": len(categorized_links)
    }
    
    if not no_cache:
        set_cached('salary_benefits', cache_params, result, ttl=ONE_DAY)
    
    total_elapsed = time.time() - start_time
    logger.info(f"Total salary_benefits took {total_elapsed:.2f}s (search: {search_elapsed:.2f}s)")
    
    return result


@router.get("/company-reviews", response_model=dict)
async def get_company_reviews(
    company: str,
    max_links: int = 6
):
    """
    Get company reviews and insights across news, culture, and career development.
    """
    start_time = time.time()
    
    cache_params = {'company': company.lower().strip()}
    cached_result = get_cached('company_reviews', cache_params)
    print(f"cache key: {cache_params}")
    print(f"cache results: {cached_result}")
    if cached_result:
        elapsed = time.time() - start_time
        logger.info(f"Cache hit for company_reviews - returned in {elapsed:.2f}s")
        return cached_result

    logger.info(f"Company reviews request: company='{company}'")

    # PASS 1: Parallel searches
    search_start = time.time()
    
    queries = {
        "news": f"{company} merges purchases earnings 2024 2025",
        "culture": f"{company} employee reviews culture work-life balance glassdoor comparably blind indeed",
        "career": f"{company} career growth promotion training development glassdoor comparably"
    }

    tasks = [
        brave_search(query, BRAVE_API_KEY, category)
        for category, query in queries.items()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    search_elapsed = time.time() - search_start
    logger.info(f"Brave searches took {search_elapsed:.2f}s")

    # PASS 2: Flatten and deduplicate
    seen_urls = set()
    all_links = []
    
    for category, result_data in zip(queries.keys(), results_list):
        if isinstance(result_data, Exception):
            logger.error(f"Error in category '{category}': {result_data}")
            continue
        
        for link in result_data:
            url = link.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_links.append({
                    "url": url,
                    "title": link.get("title", ""),
                    "description": link.get("description", ""),
                    "source_category": category
                })
    
    logger.info(f"Found {len(all_links)} unique links before filtering")

    # PASS 3: Pre-filter before GPT
    filter_start = time.time()
    
    filtered_links = filter_blacklisted(all_links)
    logger.info(f"After blacklist filter: {len(filtered_links)} links")
    
    deduplicated_links = deduplicate_by_domain(filtered_links, max_per_domain=1)
    logger.info(f"After domain dedup: {len(deduplicated_links)} links")
    
    filter_elapsed = time.time() - filter_start
    logger.info(f"Pre-filtering took {filter_elapsed:.2f}s")

    # PASS 4: Use GPT to select 6 links
    gpt_start = time.time()
    
    selected_links = await select_review_links_with_gpt(
        company,
        deduplicated_links,
        OPENAI_API_KEY,
        max_links
    )
    
    gpt_elapsed = time.time() - gpt_start
    logger.info(f"GPT selection took {gpt_elapsed:.2f}s")

    # PASS 5: Format titles for display
    formatted_links = [format_link_for_display(link) for link in selected_links]

    result = {
        "company": company,
        "links": formatted_links,
        "total_found": len(all_links)
    }

    set_cached('company_reviews', cache_params, result, ttl=SEVEN_DAYS)
    
    total_elapsed = time.time() - start_time
    logger.info(f"Total company_reviews took {total_elapsed:.2f}s (search: {search_elapsed:.2f}s, filter: {filter_elapsed:.2f}s, gpt: {gpt_elapsed:.2f}s)")
    
    return result


@router.get("/interview-prep", response_model=dict)
async def get_interview_prep(
    company: str,
    job_title: str,
    max_links: int = 6
):
    start_time = time.time()
    
    # Check cache first
    cache_params = {
        'company': company.lower().strip(),
        'job_title': job_title.lower().strip()
    }
    
    cached_result = get_cached('interview_prep', cache_params)
    if cached_result:
        elapsed = time.time() - start_time
        logger.info(f"Cache hit for interview_prep - returned in {elapsed:.2f}s")
        return cached_result
    
    logger.info(f"Interview prep request: company='{company}', job_title='{job_title}'")

    # Infer job family
    job_family = infer_job_family(job_title)
    logger.info(f"Inferred job family: {job_family}")

    # Get job family-specific queries
    queries = get_interview_prep_queries(company, job_title, job_family)
    
    # PASS 1: Parallel searches
    search_start = time.time()
    
    tasks = [
        brave_search(query, BRAVE_API_KEY, f"query_{i}")
        for i, query in enumerate(queries)
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    search_elapsed = time.time() - search_start
    logger.info(f"Brave searches took {search_elapsed:.2f}s")

    # PASS 2: Flatten and deduplicate
    seen_urls = set()
    all_links = []
    
    for i, result_data in enumerate(results_list):
        if isinstance(result_data, Exception):
            logger.error(f"Error in query {i}: {result_data}")
            continue
        
        for link in result_data:
            url = link.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_links.append({
                    "url": url,
                    "title": link.get("title", ""),
                    "description": link.get("description", ""),
                    "source_query": i
                })
    
    logger.info(f"Found {len(all_links)} unique links before filtering")

    # PASS 3: Pre-filter before GPT
    filter_start = time.time()
    
    # Remove blacklisted URLs (job postings, layoffs, etc.)
    filtered_links = filter_blacklisted(all_links)
    logger.info(f"After blacklist filter: {len(filtered_links)} links")
    
    
    # ADD THIS: Deduplicate by domain - max 1 link per domain
    deduplicated_links = deduplicate_by_domain(filtered_links, max_per_domain=1)
    logger.info(f"After domain dedup: {len(deduplicated_links)} links")
    
    filter_elapsed = time.time() - filter_start
    logger.info(f"Pre-filtering took {filter_elapsed:.2f}s")

    # PASS 4: Use GPT to select best links (now with much smaller input)
    gpt_start = time.time()

    selected_links = await select_interview_prep_links_with_gpt(
        company,
        job_title,
        deduplicated_links,  # CHANGE THIS: Pass deduplicated list
        OPENAI_API_KEY,
        max_links
    )
    
    gpt_elapsed = time.time() - gpt_start
    logger.info(f"GPT selection took {gpt_elapsed:.2f}s")

    # PASS 5: Format titles for display
    formatted_links = [format_link_for_display(link) for link in selected_links]

    result = {
        "company": company,
        "job_title": job_title,
        "job_family": job_family,
        "links": formatted_links,
        "total_found": len(all_links)
    }
    
    # Cache for 1 hour
    set_cached('interview_prep', cache_params, result, ttl=3600)
    
    total_elapsed = time.time() - start_time
    logger.info(f"Total interview_prep took {total_elapsed:.2f}s (search: {search_elapsed:.2f}s, filter: {filter_elapsed:.2f}s, gpt: {gpt_elapsed:.2f}s)")

    return result

