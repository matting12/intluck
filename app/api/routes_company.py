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
from app.utils.zipcode_to_city import zipcode_to_city


router = APIRouter()
logger = logging.getLogger(__name__)


async def select_best_links_with_gpt(
    company: str,
    all_links: list[dict],
    openai_api_key: str,
    max_links: int = 5
) -> list[dict]:
    """
    Use GPT-4o-mini to select the most relevant company information links.
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
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
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
    openai_api_key: str,
    max_links: int = 5
) -> list[dict]:
    """
    Use GPT-4o-mini to select the most relevant salary and benefits links.
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
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
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
    openai_api_key: str,
    max_links: int = 6
) -> list[dict]:
    """
    Use GPT-4o-mini to select 6 company review links (2 per category).
    """
    
    if not all_links:
        return []
    
    prompt = f"""You are analyzing search results about {company} to find insights on company news, culture, and career development.

Select {max_links} links - EXACTLY 2 FROM EACH CATEGORY:

**Company News & Updates (2 links):**
- Recent news, layoffs, restructuring, earnings reports
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
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
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
    openai_api_key: str,
    max_links: int = 6
) -> list[dict]:
    """
    Use GPT-4o-mini to select interview prep links with priority order.
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
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
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
    brave_api_key: str,
    openai_api_key: str,
    max_links: int = 5
):
    """
    Get curated company information links.
    
    Process:
    1. Identify company domain
    2. Run 4 parallel searches (about, culture, social, leadership)
    3. Flatten and deduplicate results
    4. Use GPT-4o-mini to select the top N most relevant links
    """
    logger.info(f"Company info request: company='{company}'")

    # PASS 1: Identify domain
    domain = await identify_company_domain(company, brave_api_key)
    if not domain:
        return {
            "domain": None,
            "links": [],
            "error": "Could not identify company domain"
        }

    logger.info(f"Identified domain: {domain}")

    # PASS 2: Category queries (run in parallel)
    queries = {
        "about": f"site:{domain} about us overview mission",
        "culture": f"site:{domain} culture values careers life",
        "social": f"{company} linkedin twitter instagram facebook",
        "executive": f"site:{domain} leadership team CEO executive blog",
    }

    tasks = [
        brave_search(query, brave_api_key, category)
        for category, query in queries.items()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    # PASS 3: Flatten and deduplicate
    seen_urls = set()
    all_links = []
    
    for category, result_data in zip(queries.keys(), results_list):
        if isinstance(result_data, Exception):
            logger.error(f"Error in category '{category}': {result_data}")
            continue
        
        # Assuming brave_search returns a list of dicts with url, title, description
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
    
    logger.info(f"Found {len(all_links)} unique links across all categories")

    # PASS 4: Use GPT to select best links
    selected_links = await select_best_links_with_gpt(
        company,
        all_links,
        openai_api_key,
        max_links
    )

    # Format the titles
    formatted_links = [format_link_for_display(link) for link in selected_links]

    return {
        "domain": domain,
        "links": formatted_links,
        "total_found": len(all_links)

    }

@router.get("/salary-benefits", response_model=dict)
async def get_salary_benefits(
    company: str,
    job_title: str,
    location: str,  # Can be zipcode or city
    brave_api_key: str,
    openai_api_key: str,
    max_links: int = 5
):
    logger.info(f"Salary/benefits request: company='{company}', job_title='{job_title}', location='{location}'")

    # Convert zipcode to city if it looks like a zipcode
    if location.isdigit() and len(location) == 5:
        city_state = await zipcode_to_city(location)
        logger.info(f"Converted zipcode {location} → {city_state}")
    else:
        city_state = location  # Already a city name
    
    # PASS 1: Parallel searches using city_state
    queries = {
        "salary": f"{company} {job_title} salary {city_state}",
        "benefits": f"{company} benefits 401k health insurance PTO",
        "aggregators": f"{company} {job_title} {city_state} site:levels.fyi OR site:glassdoor.com"
    }

    tasks = [
        brave_search(query, brave_api_key, category)
        for category, query in queries.items()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

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
    
    logger.info(f"Found {len(all_links)} unique links for salary/benefits")

    # PASS 3: Use GPT to select best links with salary-specific prompt
    selected_links = await select_salary_links_with_gpt(
        company,
        job_title,
        all_links,
        openai_api_key,
        max_links
    )

    # PASS 4: Format titles for display
    formatted_links = [format_link_for_display(link) for link in selected_links]

    return {
        "company": company,
        "job_title": job_title,
        "location": location,
        "links": formatted_links,
        "total_found": len(all_links)
    }

@router.get("/company-reviews", response_model=dict)
async def get_company_reviews(
    company: str,
    brave_api_key: str,
    openai_api_key: str,
    max_links: int = 6
):
    """
    Get company reviews and insights across news, culture, and career development.
    
    Process:
    1. Run 3 parallel searches for news, culture, and career topics
    2. Flatten and deduplicate results
    3. Use GPT-4o-mini to select 6 links (2 per category)
    """
    logger.info(f"Company reviews request: company='{company}'")

    # PASS 1: Parallel searches across 3 categories
    queries = {
        "news": f"{company} news layoffs restructuring earnings 2023 2024 2025",
        "culture": f"{company} employee reviews culture work-life balance glassdoor comparably blind indeed",
        "career": f"{company} career growth promotion training development glassdoor comparably"
    }

    tasks = [
        brave_search(query, brave_api_key, category)
        for category, query in queries.items()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

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
    
    logger.info(f"Found {len(all_links)} unique links for company reviews")

    # PASS 3: Use GPT to select 6 links (2 per category)
    selected_links = await select_review_links_with_gpt(
        company,
        all_links,
        openai_api_key,
        max_links
    )

    # PASS 4: Format titles for display
    formatted_links = [format_link_for_display(link) for link in selected_links]

    return {
        "company": company,
        "links": formatted_links,
        "total_found": len(all_links)
    }

@router.get("/interview-prep", response_model=dict)
async def get_interview_prep(
    company: str,
    job_title: str,
    brave_api_key: str,
    openai_api_key: str,
    max_links: int = 6
):
    """
    Get interview preparation resources for a specific role at a company.
    
    Process:
    1. Run 3 parallel searches for company-specific, role-generic, and tools/stack
    2. Flatten and deduplicate results
    3. Use GPT-4o-mini to select top 6 links with priority order
    """
    logger.info(f"Interview prep request: company='{company}', job_title='{job_title}'")

    # PASS 1: Parallel searches
    queries = {
        "company_specific": f"{company} {job_title} interview questions process glassdoor blind",
        "tech_stack": f"{company} tech stack tools technologies {job_title}",
        "role_generic": f"{job_title} interview questions technical skills preparation"
    }

    tasks = [
        brave_search(query, brave_api_key, category)
        for category, query in queries.items()
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

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
    
    logger.info(f"Found {len(all_links)} unique links for interview prep")

    # PASS 3: Use GPT to select best links with priority-based selection
    gpt_start = time.time()

    selected_links = await select_interview_prep_links_with_gpt(
        company,
        job_title,
        all_links,
        openai_api_key,
        max_links
    )
    gpt_elapsed = time.time() - gpt_start
    logger.info(f"GPT selection took {gpt_elapsed:.2f}s")

    # PASS 4: Format titles for display
    formatted_links = [format_link_for_display(link) for link in selected_links]

    return {
        "company": company,
        "job_title": job_title,
        "links": formatted_links,
        "total_found": len(all_links)
    }

