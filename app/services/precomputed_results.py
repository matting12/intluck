"""
Service for loading pre-computed company results from full-links-results.json.
Falls back to live search if company not found.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to pre-computed results
PRECOMPUTED_PATH = Path("notes/full-links-results.json")

# Cache the loaded data
_precomputed_cache = None


def _load_precomputed() -> dict:
    """Load pre-computed results, with caching."""
    global _precomputed_cache

    if _precomputed_cache is not None:
        return _precomputed_cache

    try:
        if PRECOMPUTED_PATH.exists():
            with open(PRECOMPUTED_PATH, 'r', encoding='utf-8') as f:
                _precomputed_cache = json.load(f)
                logger.info(f"Loaded {len(_precomputed_cache.get('companies', {}))} pre-computed company results")
                return _precomputed_cache
        else:
            logger.warning(f"Pre-computed results file not found: {PRECOMPUTED_PATH}")
            _precomputed_cache = {"companies": {}}
            return _precomputed_cache
    except Exception as e:
        logger.error(f"Error loading pre-computed results: {e}")
        _precomputed_cache = {"companies": {}}
        return _precomputed_cache


def get_precomputed_company_info(company_name: str) -> Optional[dict]:
    """
    Get pre-computed company info if available.

    Returns:
        Dict with 'domain' and 'links' if found, None otherwise.
    """
    data = _load_precomputed()
    companies = data.get("companies", {})

    # Try exact match first
    if company_name in companies:
        result = companies[company_name]
        if "error" not in result and result.get("links"):
            logger.info(f"Found pre-computed results for '{company_name}': {len(result.get('links', []))} links")
            return result

    # Try case-insensitive match
    company_lower = company_name.lower()
    for name, result in companies.items():
        if name.lower() == company_lower:
            if "error" not in result and result.get("links"):
                logger.info(f"Found pre-computed results for '{company_name}' (matched '{name}'): {len(result.get('links', []))} links")
                return result

    logger.info(f"No pre-computed results for '{company_name}'")
    return None


def reload_precomputed():
    """Force reload of pre-computed results (e.g., after regenerating)."""
    global _precomputed_cache
    _precomputed_cache = None
    _load_precomputed()
