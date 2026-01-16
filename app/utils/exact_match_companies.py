"""
Utility for handling companies that require exact name matching in searches.
These are typically companies with common words in their names that would
return too many irrelevant results without exact matching.
"""

# Companies that need exact phrase matching (wrapped in quotes)
# Add companies here that have generic words in their names
EXACT_MATCH_COMPANIES = {
    "Medical City Dallas",
    "Medical City Healthcare",
    "Medical City Plano",
    "Medical City Fort Worth",
    "Medical City Arlington",
    "Medical City Las Colinas",
    "Medical City McKinney",
    "Medical City Lewisville",
    "Medical City Denton",
    "Medical City Weatherford",
    "General Motors",
    "General Electric",
    "General Dynamics",
    "General Mills",
    "United Airlines",
    "United Healthcare",
    "United Technologies",
    "American Airlines",
    "American Express",
    "Delta Air Lines",
    "Blue Origin",
    "Blue Cross Blue Shield",
    "State Farm",
    "Progressive Insurance",
    "Capital One",
    "First Republic",
    "Fifth Third Bank",
    "Citizens Bank",
    "Ally Financial",
    "Discovery Inc",
    "Target Corporation",
    "Best Buy",
    "Home Depot",
    "Dollar General",
    "Dollar Tree",
    "Family Dollar",
    "Big Lots",
    "Five Below",
    "Seven Eleven",
    "Circle K",
}

# Convert to lowercase set for case-insensitive matching
_EXACT_MATCH_LOWER = {c.lower() for c in EXACT_MATCH_COMPANIES}


def needs_exact_match(company: str) -> bool:
    """
    Check if a company name requires exact phrase matching.

    Args:
        company: The company name to check

    Returns:
        True if the company should be searched as an exact phrase
    """
    return company.lower().strip() in _EXACT_MATCH_LOWER


def format_company_for_search(company: str) -> str:
    """
    Format company name for search query.
    Wraps in quotes if exact matching is needed.

    Args:
        company: The company name

    Returns:
        Formatted company name (with or without quotes)
    """
    company = company.strip()
    if needs_exact_match(company):
        return f'"{company}"'
    return company


def format_company_for_site_search(company: str, domain: str) -> str:
    """
    Format company name for site-restricted search.
    Uses exact matching when needed.

    Args:
        company: The company name
        domain: The company's domain for site: restriction

    Returns:
        Formatted search query segment
    """
    formatted_company = format_company_for_search(company)
    return f'{formatted_company} site:{domain}'
