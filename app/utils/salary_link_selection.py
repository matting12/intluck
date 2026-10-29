"""
Link selection and ordering for salary & benefits (company overview box 3).
Selects up to 9 links in strict priority order (see SLOTS):
1.   Company Website - Benefits/Total Rewards/Perks
2-3. Salary Information for job title at company
4-5. Negotiating Salary — at the company, else for the job title
6-7. Benefits & Perks Reviews from external sites
8.   Benefits video on social media
9.   Industry Benefits Comparison
"""

__all__ = ['select_salary_links']

import logging
import re
from urllib.parse import urlparse
from app.utils.salary_queries import format_salary_category_name

logger = logging.getLogger(__name__)

# Trusted domains that get a pass on title matching
TRUSTED_PASS_DOMAINS = {
    'glassdoor.com', 'levels.fyi', 'linkedin.com', 'indeed.com',
    'payscale.com', 'salary.com', 'comparably.com', 'blind.com',
    'teamblind.com', 'reddit.com', 'leetcode.com', 'github.com',
    'vault.com', 'fishbowlapp.com', 'careerbliss.com', 'greatplacetowork.com',
    'ambitionbox.com', 'bls.gov', 'h1bdata.info'
}

# Display slots in strict order: (category_key, search buckets drawn from in order,
# max links, one-link-per-domain). Missing links are dropped — no fillers.
SLOTS = [
    ('benefits_landing', ['benefits_landing'], 1, True),
    ('salary', ['salary'], 2, True),
    # Company-specific negotiation advice first, then job-title advice fills the rest
    ('negotiation', ['negotiation_company', 'negotiation_role'], 2, True),
    ('benefits_reviews', ['benefits_reviews', 'medical_benefits'], 2, True),
    ('benefits_videos', ['benefits_videos'], 1, False),
    ('industry_comparison', ['industry_comparison'], 1, True),
]

# Buckets about the job title / industry, not the company — skip the company-name check
NO_COMPANY_FILTER = {'negotiation_role', 'industry_comparison'}

# Title must show the page is actually on-topic (search engines drift to generic salary/perks pages)
NEGOTIATION_TITLE = re.compile(r'(?=.*negotiat)(?=.*\b(salary|pay|offer|compensation|raise)\b)', re.I)
TITLE_MUST_MATCH = {
    'negotiation_company': NEGOTIATION_TITLE,
    'negotiation_role': NEGOTIATION_TITLE,
    # Whole words only — "compar" alone would match the site name "Comparably"
    'industry_comparison': re.compile(
        r'(?=.*\b(compare[sd]?|comparing|comparison|vs|versus|benchmarks?|industry|average|survey)\b)'
        r'(?=.*\b(benefits?|perks?|compensation|pay|working|rewards)\b)', re.I),
    # Employee benefits, not customer loyalty perks (e.g. airline status, membership rewards)
    'benefits_videos': re.compile(r'employee|\bwork|\bjobs?\b|career|total rewards|401k|staff|hiring', re.I),
}

# Individual video/post URLs only — not channel, profile, or tag/discover pages
VIDEO_URL = re.compile(
    r'youtube\.com/(watch\?v=|shorts/)|youtu\.be/|tiktok\.com/@[^/]+/video/'
    r'|instagram\.com/(reel|p)/|linkedin\.com/(posts|feed/update)/', re.I)


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


def _is_trusted_domain(url: str) -> bool:
    """Check if URL is from a trusted domain that gets a pass on title matching."""
    domain = _extract_domain(url)
    for trusted in TRUSTED_PASS_DOMAINS:
        if domain == trusted or domain.endswith('.' + trusted):
            return True
    return False


def _company_name_in_title(title: str, company_name: str) -> bool:
    """Check if company name appears in the title as a whole word (not as a substring of another word)."""
    if not title or not company_name:
        return False

    title_lower = title.lower()
    company_lower = company_name.lower()

    # Word-boundary match: "adp" must not be immediately followed by a letter/digit
    # Prevents "ADP" matching inside "ADPI", "ADPList", etc.
    pattern = re.escape(company_lower) + r'(?![a-zA-Z0-9])'
    if re.search(pattern, title_lower):
        return True

    # For multi-word names, check the first significant word with same boundary rule
    company_words = [w for w in company_lower.split() if len(w) > 2]
    if len(company_words) > 1:
        word_pattern = re.escape(company_words[0]) + r'(?![a-zA-Z0-9])'
        return bool(re.search(word_pattern, title_lower))

    return False


def _company_name_in_url(url: str, company_name: str) -> bool:
    """Check if company name appears as a path segment in the URL (not just a substring)."""
    if not url or not company_name:
        return False
    try:
        path = urlparse(url).path.lower()
        name = company_name.lower().replace(' ', '').replace('&', '').replace('.', '')
        segments = [s for s in path.replace('-', '/').split('/') if s]
        return name in segments
    except Exception:
        return False


def _should_include_link(link: dict, company_name: str) -> bool:
    """Check if link belongs to the right company — name must appear in title or URL path."""
    if _company_name_in_title(link.get('title', ''), company_name):
        return True
    if _company_name_in_url(link.get('url', ''), company_name):
        return True
    return False


def _qualifies(link: dict, bucket: str, company_name: str) -> bool:
    pattern = TITLE_MUST_MATCH.get(bucket)
    if pattern and not pattern.search(link.get('title', '')):
        return False
    if bucket == 'benefits_videos' and not VIDEO_URL.search(link.get('url', '')):
        return False
    if not company_name or bucket in NO_COMPANY_FILTER:
        return True
    if _should_include_link(link, company_name):
        return True
    # Salary aggregators often title pages by job, not company
    return bucket == 'salary' and _is_trusted_domain(link.get('url', ''))


def select_salary_links(search_results: dict, company_name: str = None) -> list:
    """
    Fill SLOTS in order from the search buckets. Returns display-ordered links,
    each tagged with 'category' and 'category_key'. A URL is used at most once.
    """
    used_urls = set()
    ordered = []

    for category_key, buckets, max_count, distinct_domains in SLOTS:
        picked = []
        seen_domains = set()
        for bucket in buckets:
            for link in search_results.get(bucket, []):
                if len(picked) >= max_count:
                    break
                url = link.get('url', '')
                domain = _extract_domain(url)
                if not url or url in used_urls or (distinct_domains and domain in seen_domains):
                    continue
                if not _qualifies(link, bucket, company_name):
                    continue
                used_urls.add(url)
                seen_domains.add(domain)
                entry = link.copy()
                entry['category'] = format_salary_category_name(category_key)
                entry['category_key'] = category_key
                if category_key == 'benefits_videos' and ('youtube.com' in domain or domain == 'youtu.be'):
                    entry['type'] = 'video'
                picked.append(entry)
        logger.info(f"[{category_key}] {len(picked)}/{max_count} links")
        ordered.extend(picked)

    return ordered


def _demo():
    """Self-check: slot order, negotiation fallback, filters. Run: python -m app.utils.salary_link_selection"""
    company = "Delta Air Lines"
    results = {
        'benefits_landing': [{'url': 'https://www.delta.com/benefits', 'title': 'Delta Benefits & Total Rewards'}],
        'salary': [
            {'url': 'https://www.glassdoor.com/a', 'title': 'Delta Pilot Salaries'},
            {'url': 'https://www.glassdoor.com/b', 'title': 'Delta Pilot Pay'},  # same domain -> skipped
            {'url': 'https://www.levels.fyi/x', 'title': 'Pilot pay'},           # trusted, no company name -> ok
        ],
        'negotiation_company': [{'url': 'https://www.glassdoor.com/q', 'title': 'Delta: how would you negotiate with a vendor'},
                                {'url': 'https://blog.example.com/delta', 'title': 'Negotiating your Delta offer'}],
        'negotiation_role': [
            {'url': 'https://www.levels.fyi/p', 'title': 'Pilot Salaries'},  # not about negotiating
            {'url': 'https://www.reddit.com/r/pilots/1', 'title': 'How to negotiate pilot salary'},
            {'url': 'https://www.reddit.com/r/pilots/2', 'title': 'Negotiating pilot offer'},  # same domain -> skipped
            {'url': 'https://www.indeed.com/advice', 'title': 'Negotiating pilot pay'},
        ],
        'benefits_reviews': [{'url': 'https://www.glassdoor.com/r', 'title': 'Delta Benefits Reviews'},
                             {'url': 'https://www.indeed.com/r', 'title': 'United Benefits'}],  # wrong company
        'medical_benefits': [{'url': 'https://www.comparably.com/m', 'title': 'Delta Health Benefits'}],
        'benefits_videos': [{'url': 'https://www.youtube.com/watch?v=abc', 'title': 'Delta Air Lines employee perks'},
                            {'url': 'https://www.youtube.com/watch?v=zzz', 'title': 'Delta Medallion perks'},
                            {'url': 'https://www.tiktok.com/discover/delta-perks', 'title': 'Delta perks'},  # tag page
                            {'url': 'https://www.tiktok.com/@delta/video/1', 'title': 'Delta employee benefits day'},
                            {'url': 'https://www.youtube.com/watch?v=def', 'title': 'Delta 401k for employees'}],  # over cap
        'industry_comparison': [{'url': 'https://www.comparably.com/delta/perks', 'title': 'Delta Airlines Benefits | Comparably'},
                                {'url': 'https://example.com/fin', 'title': 'Delta financial benchmarks'},  # not about benefits
                                {'url': 'https://www.shrm.org/airline', 'title': 'Airline benefits benchmark'}],
    }
    links = select_salary_links(results, company_name=company)
    keys = [l['category_key'] for l in links]
    assert keys == ['benefits_landing', 'salary', 'salary', 'negotiation', 'negotiation',
                    'benefits_reviews', 'benefits_reviews', 'benefits_videos', 'industry_comparison'], keys
    neg = [l['url'] for l in links if l['category_key'] == 'negotiation']
    assert neg == ['https://blog.example.com/delta', 'https://www.reddit.com/r/pilots/1'], neg
    vids = [l for l in links if l['category_key'] == 'benefits_videos']
    assert len(vids) == 1 and vids[0]['type'] == 'video'
    assert [l['url'] for l in links][-1] == 'https://www.shrm.org/airline'
    print("ok:", keys)


if __name__ == "__main__":
    _demo()
