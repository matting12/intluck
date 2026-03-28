"""
Async company enrichment service.
When a new company is searched, this service enriches it with:
- Industry/vertical
- Official domain
- Description
- Related companies
Then appends to company_info.json and top_companies.json
"""

import asyncio
import json
import os
import logging
import httpx
from pathlib import Path
from typing import Optional
import filelock

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Track companies currently being enriched to avoid duplicates
_enrichment_in_progress = set()
_enrichment_lock = asyncio.Lock()

# File paths
DATA_DIR = Path("data")
COMPANY_INFO_PATH = DATA_DIR / "company_info.json"
TOP_COMPANIES_PATH = DATA_DIR / "top_companies.json"

# File lock for thread-safe writes
COMPANY_INFO_LOCK = DATA_DIR / ".company_info.lock"


def _load_company_info() -> dict:
    """Load current company_info.json"""
    try:
        with open(COMPANY_INFO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading company_info.json: {e}")
        return {}


def _load_top_companies() -> list:
    """Load current top_companies.json"""
    try:
        with open(TOP_COMPANIES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading top_companies.json: {e}")
        return []


def _save_company_info(data: dict):
    """Save company_info.json with file locking"""
    lock = filelock.FileLock(str(COMPANY_INFO_LOCK), timeout=10)
    try:
        with lock:
            with open(COMPANY_INFO_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving company_info.json: {e}")


def _save_top_companies(data: list):
    """Save top_companies.json"""
    try:
        with open(TOP_COMPANIES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving top_companies.json: {e}")


def is_known_company(company_name: str) -> bool:
    """Check if company is already in our database"""
    company_info = _load_company_info()
    company_lower = company_name.lower().strip()

    for known in company_info.keys():
        if known.lower() == company_lower:
            return True
    return False


async def enrich_company_via_search(company_name: str) -> Optional[dict]:
    """
    Fallback: Use Brave Search to get basic company info.
    Less accurate than LLM but doesn't require OpenAI API.
    """
    if not BRAVE_API_KEY:
        logger.warning("BRAVE_API_KEY not set, skipping search enrichment")
        return None

    try:
        async with httpx.AsyncClient() as client:
            # Search for company official site
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": BRAVE_API_KEY
                },
                params={
                    "q": f"{company_name} official website",
                    "count": 10,
                    "search_lang": "en",
                    "country": "us"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("web", {}).get("results", [])
            if not results:
                return None

            # Find first non-wikipedia/linkedin/glassdoor result for domain
            from urllib.parse import urlparse
            skip_domains = ['wikipedia.org', 'linkedin.com', 'glassdoor.com', 'indeed.com',
                           'crunchbase.com', 'bloomberg.com', 'forbes.com', 'yahoo.com']

            domain = None
            description = None

            for result in results:
                url = result.get("url", "")
                parsed = urlparse(url)
                result_domain = parsed.netloc.replace("www.", "")

                # Skip aggregator sites
                if any(skip in result_domain for skip in skip_domains):
                    continue

                domain = result_domain
                description = result.get("description", "")[:100]
                break

            if not domain:
                # Fallback to first result
                first_url = results[0].get("url", "")
                parsed = urlparse(first_url)
                domain = parsed.netloc.replace("www.", "")
                description = results[0].get("description", "")

            # Clean up description
            if description:
                # Remove HTML tags and get first sentence
                import re
                description = re.sub(r'<[^>]+>', '', description)
                description = description.split(".")[0].strip()

            return {
                "full_name": company_name,
                "description": description or f"{company_name} company",
                "domain": domain,
                "industry": "Unknown",  # Can't determine from search
                "related": []
            }

    except Exception as e:
        logger.error(f"Error enriching via search '{company_name}': {e}")
        return None


async def enrich_company(company_name: str) -> Optional[dict]:
    """
    Use LLM to enrich company data.
    Returns dict with: full_name, description, industry, domain, related
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set, skipping enrichment")
        return None

    prompt = f"""You are a business analyst. Provide information about this company: "{company_name}"

Return ONLY valid JSON with these fields:
{{
    "full_name": "Official full company name",
    "description": "Brief 10-15 word description of what the company does",
    "industry": "Primary industry (e.g., Technology, Finance, Healthcare, Retail, Consulting, etc.)",
    "domain": "Official website domain (e.g., google.com, not www.google.com)",
    "related": ["Up to 3 similar/competitor companies"]
}}

If you don't recognize the company, make your best guess based on the name.
Return ONLY the JSON object, no markdown, no explanation."""

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
                            "content": "You are a business data assistant. Return only valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 300
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

            enriched = json.loads(content)
            logger.info(f"Enriched company '{company_name}': {enriched.get('industry', 'Unknown')}")
            return enriched

    except Exception as e:
        logger.error(f"Error enriching company via LLM '{company_name}': {e}")
        # Fall back to search-based enrichment
        logger.info(f"Falling back to search-based enrichment for '{company_name}'")
        return await enrich_company_via_search(company_name)


async def enrich_and_save_company(company_name: str):
    """
    Main entry point: enrich a company and save to JSON files.
    Handles deduplication and concurrent access.
    """
    company_name = company_name.strip()

    # Skip if already known
    if is_known_company(company_name):
        logger.debug(f"Company '{company_name}' already in database, skipping enrichment")
        return

    # Skip if enrichment already in progress for this company
    async with _enrichment_lock:
        if company_name.lower() in _enrichment_in_progress:
            logger.debug(f"Enrichment already in progress for '{company_name}'")
            return
        _enrichment_in_progress.add(company_name.lower())

    try:
        # Enrich via LLM
        enriched = await enrich_company(company_name)

        if not enriched:
            logger.warning(f"Could not enrich company '{company_name}'")
            return

        # Prepare company info entry
        company_entry = {
            "full_name": enriched.get("full_name", company_name),
            "description": enriched.get("description", ""),
        }

        # Add optional fields if present
        if enriched.get("related"):
            company_entry["related"] = enriched["related"]
        if enriched.get("industry"):
            company_entry["industry"] = enriched["industry"]
        if enriched.get("domain"):
            company_entry["domain"] = enriched["domain"]

        # Save to company_info.json
        company_info = _load_company_info()
        company_info[company_name] = company_entry
        _save_company_info(company_info)

        # Add to top_companies.json for autocomplete
        top_companies = _load_top_companies()
        if company_name not in top_companies:
            top_companies.append(company_name)
            top_companies.sort(key=str.lower)
            _save_top_companies(top_companies)

        logger.info(f"Added new company to database: '{company_name}' ({enriched.get('industry', 'Unknown')})")

    finally:
        # Remove from in-progress set
        async with _enrichment_lock:
            _enrichment_in_progress.discard(company_name.lower())


def sync_enrich_and_save_company(company_name: str):
    """
    Synchronous wrapper for background task execution.
    Called by FastAPI BackgroundTasks.
    """
    logger.info(f"Background task started for '{company_name}'")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(enrich_and_save_company(company_name))
        loop.close()
        logger.info(f"Background task completed for '{company_name}'")
    except Exception as e:
        logger.error(f"Error in background enrichment for '{company_name}': {e}")
        import traceback
        traceback.print_exc()
