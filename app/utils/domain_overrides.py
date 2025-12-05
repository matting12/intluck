"""
Manual domain overrides for companies with ambiguous results.
"""

__all__ = ['get_domain_override']

DOMAIN_OVERRIDES = {
    'microsoft': 'microsoft.com',
    'amazon': 'amazon.com',
    'google': 'about.google',
    'meta': 'meta.com',
    'facebook': 'meta.com',
    'apple': 'apple.com',
    'tesla': 'tesla.com',
    'netflix': 'netflix.com',
    'walmart': 'walmart.com',
    'target': 'target.com',
    'starbucks': 'starbucks.com',
    'mcdonalds': 'mcdonalds.com',
    'coca-cola': 'coca-cola.com',
    'pepsi': 'pepsi.com',
    'nike': 'nike.com',
    'adidas': 'adidas.com',
    'intel': 'intel.com',
    'amd': 'amd.com',
    'nvidia': 'nvidia.com',
    'ibm': 'ibm.com',
    'oracle': 'oracle.com',
    'salesforce': 'salesforce.com',
    'adobe': 'adobe.com',
    'samsung': 'samsung.com',
    'sony': 'sony.com',
    'jpmorgan': 'jpmorganchase.com',
    'goldman sachs': 'goldmansachs.com',
    'morgan stanley': 'morganstanley.com',
    'bank of america': 'bankofamerica.com',
    'wells fargo': 'wellsfargo.com',
    'citigroup': 'citigroup.com',
    'deloitte': 'deloitte.com',
    'pwc': 'pwc.com',
    'ey': 'ey.com',
    'kpmg': 'kpmg.com',
    'mckinsey': 'mckinsey.com',
    'bcg': 'bcg.com',
    'bain': 'bain.com',
}

def get_domain_override(company: str) -> str | None:
    """
    Check if company has a known domain override.
    Returns domain if found, None otherwise.
    """
    normalized = company.lower().strip()
    return DOMAIN_OVERRIDES.get(normalized)