from fastapi import APIRouter, HTTPException
import logging

from app.utils.file_loader import load_json_file

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache for companies list
_companies_cache = None

def get_companies():
    global _companies_cache
    if _companies_cache is None:
        _companies_cache = load_json_file("data/top_companies.json")
    return _companies_cache


@router.get("/job-title")
async def autocomplete_job_title(q: str):
    logger.info(f"Autocomplete request: q='{q}'")

    try:
        job_titles = load_json_file("data/job_family.json")
    except Exception as e:
        logger.error(f"Error loading job_family.json: {e}")
        raise HTTPException(status_code=500, detail="Job title config error")

    query = q.lower()
    matches = [t for t in job_titles.keys() if query in t.lower()]
    results = matches[:10]

    logger.info(f"Found {len(matches)} matches, returning {len(results)}")
    return results


@router.get("/company")
async def autocomplete_company(q: str):
    logger.info(f"Company autocomplete request: q='{q}'")

    try:
        companies = get_companies()
    except Exception as e:
        logger.error(f"Error loading top_companies.json: {e}")
        raise HTTPException(status_code=500, detail="Company config error")

    query = q.lower()
    # Prioritize matches that start with the query, then contains
    starts_with = [c for c in companies if c.lower().startswith(query)]
    contains = [c for c in companies if query in c.lower() and not c.lower().startswith(query)]
    matches = starts_with + contains
    results = matches[:10]

    logger.info(f"Found {len(matches)} company matches, returning {len(results)}")
    return results
