__all__ = [
    'TRUSTED_DOMAINS',
    'DOMAIN_CONFIDENCE_SCORES',
    'is_trusted_domain',
    'get_domain_confidence',
    'filter_to_trusted_domains',
    'extract_domain'
]

from urllib.parse import urlparse

# Confidence scores: Official/authoritative = 10, Professional = 7, User-generated = 5, Social = 3
DOMAIN_CONFIDENCE_SCORES = {
    # Official data sources (10)
    "bls.gov": 10,
    "onetonline.org": 10,
    "careeronestop.org": 10,
    "dol.gov": 10,
    "sec.gov": 10,
    
    # Professional job/salary platforms (8)
    "glassdoor.com": 8,
    "levels.fyi": 8,
    "linkedin.com": 8,
    "indeed.com": 8,
    "payscale.com": 8,
    "salary.com": 8,
    "comparably.com": 8,
    "shrm.org": 8,
    
    # Tech-specific (8)
    "github.com": 8,
    "leetcode.com": 8,
    "hackerrank.com": 8,
    "dice.com": 8,
    "geeksforgeeks.org": 7,
    "careercup.com": 7,
    
    # Professional reviews (7)
    "vault.com": 7,
    "repvue.com": 7,
    "blind.com": 7,
    "teamblind.com": 7,
    "fishbowlapp.com": 7,
    "fairygodboss.com": 7,
    "inhersight.com": 7,
    "greatplacetowork.com": 7,
    "kununu.com": 7,
    "ambitionbox.com": 7,
    "careerbliss.com": 7,
    "themuse.com": 7,
    "wellfound.com": 7,
    "thejobcrowd.com": 7,
    "joberty.com": 7,
    "ivyexec.com": 7,
    
    # General job boards (6)
    "totaljobs.com": 6,
    "idealist.org": 6,
    "jobcase.com": 6,
    
    # Data/research (6)
    "h1bdata.info": 6,
    "dnb.com": 6,
    "salarytransparentstreet.com": 6,
    
    # Interview prep (6)
    "interviewbuddy.net": 6,
    "careervillage.org": 6,
    
    # User-generated/forums (5)
    "reddit.com": 5,
    "quora.com": 5,
    
    # Social media (3)
    "tiktok.com": 3,
    "instagram.com": 3,
    "snapchat.com": 3,
    "meta.com": 3,
    "buffer.com": 3
}

# Simple list for quick lookups
TRUSTED_DOMAINS = set(DOMAIN_CONFIDENCE_SCORES.keys())


def extract_domain(url: str) -> str:
    """Extract base domain from URL, removing www prefix"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_trusted_domain(url: str) -> bool:
    """Check if URL is from a trusted domain"""
    domain = extract_domain(url)
    
    # Check exact match
    if domain in TRUSTED_DOMAINS:
        return True
    
    # Check if subdomain of trusted domain (e.g., jobs.lever.co)
    for trusted in TRUSTED_DOMAINS:
        if domain.endswith('.' + trusted) or domain == trusted:
            return True
    
    return False


def get_domain_confidence(url: str) -> int:
    """Get confidence score for a URL's domain. Returns 0 if not trusted."""
    domain = extract_domain(url)
    
    # Check exact match
    if domain in DOMAIN_CONFIDENCE_SCORES:
        return DOMAIN_CONFIDENCE_SCORES[domain]
    
    # Check parent domain
    for trusted, score in DOMAIN_CONFIDENCE_SCORES.items():
        if domain.endswith('.' + trusted):
            return score
    
    return 0


def filter_to_trusted_domains(links: list[dict], min_confidence: int = 0) -> list[dict]:
    """
    Filter links to only trusted domains.
    
    Args:
        links: List of link dicts with 'url' key
        min_confidence: Minimum confidence score (0 = all trusted, 5 = no social, etc.)
    
    Returns:
        Filtered list with 'confidence' score added to each link
    """
    filtered = []
    
    for link in links:
        url = link.get('url', '')
        confidence = get_domain_confidence(url)
        
        if confidence >= min_confidence and confidence > 0:
            link['confidence'] = confidence
            link['domain'] = extract_domain(url)
            filtered.append(link)
    
    # Sort by confidence (highest first)
    filtered.sort(key=lambda x: x['confidence'], reverse=True)
    
    return filtered


# URLs to always exclude (job postings, login pages, etc.)
URL_BLACKLIST_PATTERNS = [
    '/jobs/',
    '/careers/apply',
    '/job/',
    '/positions/',
    '/apply/',
    '/login',
    '/signin',
    '/signup',
    '/register',
    '/in/',  # LinkedIn individual profiles
]

TITLE_BLACKLIST_PATTERNS = [
    'layoff',
    'layoffs',
    'lay off',
    'lay offs',
    'downsizing',
    'job cuts',
    'workforce reduction'
]


def is_blacklisted(link: dict) -> bool:
    """Check if link should be excluded based on URL or title patterns"""
    url = link.get('url', '').lower()
    title = link.get('title', '').lower()
    
    # Check URL patterns
    for pattern in URL_BLACKLIST_PATTERNS:
        if pattern in url:
            return True
    
    # Check title patterns
    for pattern in TITLE_BLACKLIST_PATTERNS:
        if pattern in title:
            return True
    
    return False


def filter_blacklisted(links: list[dict]) -> list[dict]:
    """Remove blacklisted links"""
    return [link for link in links if not is_blacklisted(link)]

def deduplicate_by_domain(links: list[dict], max_per_domain: int = 1) -> list[dict]:
    """Keep only top N links per domain, sorted by confidence"""
    from collections import defaultdict
    
    domain_groups = defaultdict(list)
    for link in links:
        domain = link.get('domain') or extract_domain(link.get('url', ''))
        domain_groups[domain].append(link)
    
    result = []
    for domain, domain_links in domain_groups.items():
        domain_links.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        result.extend(domain_links[:max_per_domain])
    
    result.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    return result

