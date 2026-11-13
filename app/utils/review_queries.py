"""
Query builders for company news & reviews (company overview box 4, "3 C's").
One query per slot, in strict display order:
1. Recent news: layoffs, restructuring, growth, mergers, acquisitions  (news_business)
2. Most recent financial performance                                  (financials)
3. Recent news on executive leadership                                (leadership)
4. Reviews on culture                                                 (culture)
5. Reviews on work-life balance                                       (work_life)
6. Reviews on diversity / DEI                                         (diversity)
7. Reviews on career development, promotion, internal mobility        (career)
8. Reviews on tuition reimbursement                                   (tuition)
"""

from app.utils.exact_match_companies import format_company_for_search
from app.utils.salary_queries import REVIEW_SITES

__all__ = ['build_review_queries', 'format_review_category_name', 'NEWS_CATEGORIES']

# Slots that need fresh results (searched with a past-year freshness filter)
NEWS_CATEGORIES = {'news_business', 'financials', 'leadership'}


def format_review_category_name(category_key: str, company: str = '') -> str:
    """Section heading for the box 4 layout; news headings lead with the company name."""
    prefix = f'{company} ' if company else ''
    return {
        'news_business': f'{prefix}Recent News',
        'financials': f'{prefix}Financial News',
        'leadership': f'{prefix}Executive Leadership News',
        'culture': 'Reviews on Company Culture',
        'work_life': 'Reviews on Work Life Balance',
        'diversity': 'Reviews on Diversity, Equity, and Inclusion',
        'career': 'Reviews on Career Development and Internal Mobility',
        'tuition': 'Reviews on Tuition Reimbursement',
    }.get(category_key, category_key.replace('_', ' ').title())


def build_review_queries(company: str) -> dict:
    """Returns: {category_key: search_query_string}"""
    c = format_company_for_search(company)
    return {
        'news_business': f'{c} (layoffs OR "job cuts" OR restructuring OR reorganization OR growth OR expansion OR merger OR acquisition OR acquires) news',
        'financials': f'{c} (quarterly OR annual OR fiscal) (earnings OR results OR revenue OR "financial results")',
        'leadership': f'{c} (CEO OR "chief executive" OR executive OR president) (appoints OR names OR "steps down" OR successor OR leadership)',
        'culture': f'{c} (culture OR "company culture") (reviews OR ratings) {REVIEW_SITES}',
        'work_life': f'{c} ("work life balance" OR "work-life balance") (reviews OR ratings) {REVIEW_SITES}',
        'diversity': f'{c} (diversity OR DEI OR inclusion) (reviews OR ratings OR score) {REVIEW_SITES}',
        'career': f'{c} ("career development" OR "career growth" OR promotion OR "internal mobility" OR advancement) (reviews OR employees) {REVIEW_SITES}',
        'tuition': f'{c} ("tuition reimbursement" OR "tuition assistance" OR "education assistance")',
    }
