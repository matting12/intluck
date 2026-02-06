from fastapi import APIRouter, HTTPException
import logging

from app.utils.file_loader import load_json_file

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache for companies list
_companies_cache = None
_company_info_cache = None

def get_companies():
    global _companies_cache
    if _companies_cache is None:
        _companies_cache = load_json_file("data/top_companies.json")
    return _companies_cache

def get_company_info():
    global _company_info_cache
    if _company_info_cache is None:
        try:
            _company_info_cache = load_json_file("data/company_info.json")
        except:
            _company_info_cache = {}
    return _company_info_cache


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


@router.get("/company-confirm")
async def confirm_company(q: str):
    """
    Returns company matching suggestions for confirmation popup.
    Used when user submits the search form to verify company name.
    """
    logger.info(f"Company confirmation request: q='{q}'")

    try:
        companies = get_companies()
        company_info = get_company_info()
    except Exception as e:
        logger.error(f"Error loading company data: {e}")
        raise HTTPException(status_code=500, detail="Company config error")

    query = q.strip()
    query_lower = query.lower()
    query_upper = query.upper()

    # Helper to get company details
    def get_details(company_name):
        info = company_info.get(company_name, {})
        return {
            "full_name": info.get("full_name"),
            "description": info.get("description")
        }

    # Check for exact match (case-insensitive)
    exact_match = None
    exact_match_details = None
    exact_match_info = None
    for c in companies:
        if c.lower() == query_lower:
            exact_match = c
            exact_match_details = get_details(c)
            exact_match_info = company_info.get(c, {})
            break

    # Find similar matches
    # 1. Starts with query
    starts_with = [c for c in companies if c.lower().startswith(query_lower) and c.lower() != query_lower]

    # 2. Contains query (but doesn't start with)
    contains = [c for c in companies if query_lower in c.lower() and not c.lower().startswith(query_lower)]

    # 3. Query might be an acronym - check if it matches initials of any company
    # Works with uppercase (IBM), mixed case (PwC), or lowercase (ibm)
    acronym_matches = []
    if len(query) <= 6:
        for c in companies:
            # Get initials (first letter of each word)
            words = c.replace('&', ' ').replace('-', ' ').split()
            initials = ''.join(word[0].upper() for word in words if word)
            if initials == query_upper and c.lower() != query_lower:
                acronym_matches.append(c)

    # 4. Get explicitly related companies from company_info
    related_matches = []

    # First, check if exact match has explicit related companies
    if exact_match_info:
        explicit_related = exact_match_info.get("related", [])
        for rel in explicit_related:
            # Find in companies list (case-insensitive)
            for c in companies:
                if c.lower() == rel.lower() and c not in related_matches:
                    related_matches.append(c)
                    break

        # Also check also_known_as
        also_known = exact_match_info.get("also_known_as", [])
        for aka in also_known:
            for c in companies:
                if c.lower() == aka.lower() and c not in related_matches:
                    related_matches.append(c)
                    break

    # Also check company_info for companies that list query in their related or also_known_as
    for company_name, info in company_info.items():
        if company_name.lower() == query_lower:
            continue
        # Check if query appears in this company's related or also_known_as
        related_list = info.get("related", [])
        aka_list = info.get("also_known_as", [])
        if query in related_list or query in aka_list:
            # Find company in our list
            for c in companies:
                if c.lower() == company_name.lower() and c not in related_matches:
                    related_matches.append(c)
                    break

    # 5. Fuzzy matches - words from query appear in company name
    query_words = set(query_lower.split())
    fuzzy_matches = []
    if len(query_words) > 1:
        for c in companies:
            c_lower = c.lower()
            if c_lower != query_lower and not c_lower.startswith(query_lower) and query_lower not in c_lower:
                c_words = set(c_lower.replace('&', ' ').replace('-', ' ').split())
                if query_words & c_words:  # If any words match
                    fuzzy_matches.append(c)

    # Combine suggestions (remove duplicates, limit count)
    seen = set()
    suggestions = []

    # Add acronym matches first (most likely to cause confusion)
    for c in acronym_matches:
        if c not in seen:
            details = get_details(c)
            suggestions.append({
                "name": c,
                "reason": "acronym",
                "full_name": details["full_name"],
                "description": details["description"]
            })
            seen.add(c)

    # Add related matches (from company_info cross-references)
    for c in related_matches[:3]:
        if c not in seen:
            details = get_details(c)
            suggestions.append({
                "name": c,
                "reason": "related",
                "full_name": details["full_name"],
                "description": details["description"]
            })
            seen.add(c)

    # Add starts_with matches
    for c in starts_with[:5]:
        if c not in seen:
            details = get_details(c)
            suggestions.append({
                "name": c,
                "reason": "similar",
                "full_name": details["full_name"],
                "description": details["description"]
            })
            seen.add(c)

    # Add contains matches
    for c in contains[:3]:
        if c not in seen:
            details = get_details(c)
            suggestions.append({
                "name": c,
                "reason": "similar",
                "full_name": details["full_name"],
                "description": details["description"]
            })
            seen.add(c)

    # Add fuzzy matches
    for c in fuzzy_matches[:2]:
        if c not in seen:
            details = get_details(c)
            suggestions.append({
                "name": c,
                "reason": "partial",
                "full_name": details["full_name"],
                "description": details["description"]
            })
            seen.add(c)

    # Determine if confirmation is needed
    needs_confirmation = (
        exact_match is None or
        len(acronym_matches) > 0 or
        len(related_matches) > 0 or
        (len(query) <= 3 and len(suggestions) > 0)
    )

    result = {
        "query": query,
        "exact_match": exact_match,
        "exact_match_full_name": exact_match_details["full_name"] if exact_match_details else None,
        "exact_match_description": exact_match_details["description"] if exact_match_details else None,
        "suggestions": suggestions[:8],  # Limit to 8 suggestions
        "needs_confirmation": needs_confirmation,
        "is_in_database": exact_match is not None
    }

    logger.info(f"Company confirmation: exact_match={exact_match}, suggestions={len(suggestions)}, needs_confirmation={needs_confirmation}")
    return result
