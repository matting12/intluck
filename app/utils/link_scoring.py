"""
Link scoring system for quality-based filtering.
Returns only links that meet a minimum quality threshold.
"""

import re
import logging
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = [
    'score_link',
    'score_and_filter_links',
    'DEFAULT_THRESHOLD'
]

DEFAULT_THRESHOLD = 45

# Domain confidence scores (adjusted per client feedback)
# Glassdoor slightly lower, unknown sites get base score
DOMAIN_SCORES = {
    # Official data sources (25)
    "bls.gov": 25,
    "sec.gov": 25,
    "dol.gov": 25,

    # Professional platforms (20) - slightly reduced from before
    "glassdoor.com": 20,
    "levels.fyi": 22,
    "linkedin.com": 18,
    "indeed.com": 18,
    "payscale.com": 20,
    "salary.com": 20,
    "comparably.com": 20,
    "blind.com": 20,
    "teamblind.com": 20,

    # Tech-specific (18)
    "github.com": 18,
    "leetcode.com": 18,
    "hackerrank.com": 16,

    # Professional reviews (16)
    "vault.com": 16,
    "repvue.com": 16,
    "fishbowlapp.com": 14,
    "fairygodboss.com": 14,
    "inhersight.com": 14,
    "greatplacetowork.com": 16,
    "themuse.com": 14,

    # User-generated (12) - higher than before for interesting content
    "reddit.com": 14,
    "quora.com": 10,

    # News/media (12)
    "youtube.com": 15,
    "vimeo.com": 12,

    # Generic job boards (10)
    "zippia.com": 10,
    "careerbliss.com": 10,
}

# Base score for unknown domains (client wants these higher)
UNKNOWN_DOMAIN_BASE_SCORE = 12


def _extract_domain(url: str) -> str:
    """Extract base domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def _get_domain_score(url: str) -> int:
    """Get domain confidence score (0-25)."""
    domain = _extract_domain(url)

    # Check exact match
    if domain in DOMAIN_SCORES:
        return DOMAIN_SCORES[domain]

    # Check parent domain (e.g., news.company.com)
    for known_domain, score in DOMAIN_SCORES.items():
        if domain.endswith('.' + known_domain):
            return score

    # Unknown domain gets base score (not zero)
    return UNKNOWN_DOMAIN_BASE_SCORE


def _company_name_score(title: str, company_name: str) -> int:
    """Score based on company name presence in title (0-25)."""
    if not title or not company_name:
        return 0

    title_lower = title.lower()
    company_lower = company_name.lower()

    # Full company name match
    if company_lower in title_lower:
        return 25

    # Partial match (first word of multi-word company)
    # Give full credit since brand name (Bell, Google, etc.) IS the company
    company_words = [w for w in company_lower.split() if len(w) > 2]
    if company_words and company_words[0] in title_lower:
        return 25  # Full credit - "Bell Newsroom" is just as good as "Bell Helicopter"

    return 0


def _title_relevance_score(title: str, category: str = None) -> int:
    """Score based on title relevance to category (0-20)."""
    if not title:
        return 0

    title_lower = title.lower()
    score = 5  # Base score for having a title

    # Category-specific keywords
    category_keywords = {
        'interview': ['interview', 'questions', 'hiring', 'process', 'experience', 'prep'],
        'salary': ['salary', 'compensation', 'pay', 'wage', 'benefits', 'perks', 'total rewards'],
        'culture': ['culture', 'values', 'work-life', 'environment', 'team', 'life at'],
        'about': ['about', 'overview', 'company', 'mission', 'history', 'leadership', 'newsroom'],
        'reviews': ['review', 'rating', 'employee', 'glassdoor', 'feedback', 'comparably'],
        'career': ['career', 'growth', 'development', 'promotion', 'training', 'careers'],
    }

    # Check for category-specific keywords
    if category:
        category_key = category.lower().split()[0] if category else ''
        keywords = category_keywords.get(category_key, [])
        for kw in keywords:
            if kw in title_lower:
                score += 5
                break

    # General quality indicators
    quality_keywords = ['guide', 'complete', 'official', 'comprehensive', '2024', '2025', '2026', 'documentary', 'inside']
    for kw in quality_keywords:
        if kw in title_lower:
            score += 3
            break

    # Penalize vague titles
    vague_titles = ['home', 'welcome', 'page', 'untitled', 'index']
    for vague in vague_titles:
        if title_lower == vague or title_lower.startswith(vague + ' '):
            score -= 10
            break

    return max(0, min(20, score))


def _description_quality_score(description: str) -> int:
    """Score based on description quality (0-15)."""
    if not description:
        return 0

    score = 0
    desc_len = len(description)

    # Length scoring
    if desc_len > 150:
        score += 8
    elif desc_len > 80:
        score += 5
    elif desc_len > 40:
        score += 2

    # Contains specific data indicators
    if re.search(r'\$[\d,]+', description):  # Dollar amounts
        score += 4
    if re.search(r'\d+%', description):  # Percentages
        score += 3
    if re.search(r'20(2[3-6])', description):  # Recent years
        score += 2

    return min(15, score)


def _freshness_score(url: str, description: str) -> int:
    """Score based on content freshness (0-10)."""
    current_year = datetime.now().year
    text = f"{url} {description or ''}".lower()

    # Check for year mentions
    if str(current_year) in text:
        return 10
    if str(current_year - 1) in text:
        return 7
    if str(current_year - 2) in text:
        return 4

    # No year indicator - neutral score
    return 5


def _url_quality_score(url: str) -> int:
    """Score based on URL structure quality (0-5)."""
    if not url:
        return 0

    score = 3  # Base score
    url_lower = url.lower()

    # Clean, semantic paths are good
    good_paths = ['/about', '/careers', '/culture', '/benefits', '/interview', '/salary', '/review']
    for path in good_paths:
        if path in url_lower:
            score += 2
            break

    # Query-heavy URLs are worse
    if '?' in url and url.count('&') > 2:
        score -= 2

    # Very long URLs are suspicious
    if len(url) > 200:
        score -= 1

    return max(0, min(5, score))


def score_link(link: dict, company_name: str = None, category: str = None) -> dict:
    """
    Score a single link and return it with score attached.

    Score breakdown (0-100):
    - Domain confidence: 0-25
    - Company name in title: 0-25
    - Title relevance: 0-20
    - Description quality: 0-15
    - Freshness: 0-10
    - URL quality: 0-5

    Returns:
        Link dict with 'score' and 'score_breakdown' fields added
    """
    url = link.get('url', '')
    title = link.get('title', '')
    description = link.get('description', '')
    link_category = category or link.get('category', '')

    # Calculate component scores
    domain_score = _get_domain_score(url)
    company_score = _company_name_score(title, company_name) if company_name else 15
    title_score = _title_relevance_score(title, link_category)
    desc_score = _description_quality_score(description)
    fresh_score = _freshness_score(url, description)
    url_score = _url_quality_score(url)

    total_score = domain_score + company_score + title_score + desc_score + fresh_score + url_score

    # Create scored link
    scored_link = link.copy()
    scored_link['score'] = total_score
    scored_link['score_breakdown'] = {
        'domain': domain_score,
        'company_match': company_score,
        'title_relevance': title_score,
        'description': desc_score,
        'freshness': fresh_score,
        'url_quality': url_score
    }

    return scored_link


def score_and_filter_links(
    links: list[dict],
    company_name: str = None,
    category: str = None,
    threshold: int = DEFAULT_THRESHOLD,
    max_links: int = None
) -> tuple[list[dict], list[dict]]:
    """
    Score all links and filter by threshold.

    Args:
        links: List of link dicts
        company_name: Company name for matching
        category: Category for relevance scoring
        threshold: Minimum score to include (default 65)
        max_links: Maximum links to return (None = no limit)

    Returns:
        Tuple of (filtered_links, all_scored_links)
        - filtered_links: Links above threshold, sorted by score
        - all_scored_links: All links with scores, for "more links" feature
    """
    if not links:
        return [], []

    # Score all links
    scored_links = [
        score_link(link, company_name, category)
        for link in links
    ]

    # Sort by score descending
    scored_links.sort(key=lambda x: x.get('score', 0), reverse=True)

    # Filter by threshold
    filtered = [link for link in scored_links if link.get('score', 0) >= threshold]

    # Apply max limit if specified
    if max_links and len(filtered) > max_links:
        filtered = filtered[:max_links]

    logger.info(f"Scoring: {len(links)} links -> {len(filtered)} above threshold ({threshold})")

    return filtered, scored_links
