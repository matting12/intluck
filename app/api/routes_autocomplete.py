from fastapi import APIRouter, HTTPException
import logging

from app.utils.file_loader import load_json_file

router = APIRouter()
logger = logging.getLogger(__name__)

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
