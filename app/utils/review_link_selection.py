"""
Link selection and ordering for company news & reviews (company overview box 4).
One link per slot, in strict order (see SLOTS). Each link must name the company
and have an on-topic title or URL; slots with no qualifying link are dropped.
"""

import logging
import re
from datetime import date, timedelta
from app.utils.review_queries import NEWS_CATEGORIES, format_review_category_name
from app.utils.salary_link_selection import _should_include_link

__all__ = ['select_review_links']

logger = logging.getLogger(__name__)

# (category_key, title/URL must match) — display order
SLOTS = [
    ('news_business', r'layoff|job cuts|cuts? jobs|restructur|reorganiz|growth|grow|expan|merger|merge|acqui|buys|deal'),
    ('financials', r'earnings|revenue|results|quarter|\bq[1-4]\b|fiscal|profit|sales|guidance'),
    # A leadership *change* (role + verb), not an org chart or "meet our leaders" page
    ('leadership', r'(?=.*(\bceo\b|chief|executive|president|chair|\bc[fot]o\b|partners?|leader))'
                   r'(?=.*(appoint|\bnames?\b|named|steps? down|stepping down|depart|retir|succe|\bhires?\b|hired'
                   r'|joins|resign|promot|transition|leadership changes))'),
    ('culture', r'culture'),
    ('work_life', r'work[\s/-]*life|balance'),
    ('diversity', r'diversity|\bdei\b|inclusion|equity|\bd&i\b'),
    ('career', r'career|promotion|advancement|mobility|development|growth opportunit'),
    ('tuition', r'tuition|education assistance|education reimbursement'),
]

# Pages that match the topic but aren't news: acquisition directories ("List of 16
# Acquisitions by ..."), company profile / "growth & outlook" pages, and law firms' M&A /
# restructuring practice pages and client publications
EXCLUDE = {
    'news_business': re.compile(r'^list of|\bprofile\b|outlook|stability|\blawyers?\b|\bpractice\b|bulletin', re.I),
    'financials': re.compile(r'ranking|league table', re.I),
    'leadership': re.compile(r'\bprofile\b|org chart', re.I),
}
EXCLUDE_URL = {
    'news_business': re.compile(r'/(insights?|publications?|practices?)/|client-memos', re.I),
}

# Open-web slots need the specific company name, not just its first word — otherwise
# "Jones Day" pulls in Dow Jones and "Fidelity Investments" pulls in FIS. Review-site
# slots stay lenient: those pages are company-scoped and often use the short name.
STRICT_NAME_SLOTS = {'news_business', 'financials', 'leadership', 'diversity', 'tuition'}

# News older than this is dropped. Brave's past-year freshness filter still lets old
# articles through ("Sundar Pichai named CEO" from 2019, Bezos stepping down in 2021).
MAX_NEWS_AGE = timedelta(days=548)  # ~18 months
URL_DATE = re.compile(r'/(20\d\d)/(?:(\d\d)(?=[/_-]|\d\d))?')  # /2020/03/16/, /2025/0402_, /2026/
TITLE_YEARS = re.compile(r'\b(20\d\d)\b')


def _published(link: dict):
    """
    Best guess at when a page was published: the date in its URL, else the latest
    year in its title ("Revenue 1991-2026"). None if unknown. (Brave's page_age is
    no use here: it's the last crawl/modify date, so a 2024 article reads as 2026.)
    """
    m = URL_DATE.search(link.get('url', ''))
    if m:
        return date(int(m[1]), int(m[2] or 1), 1)
    years = TITLE_YEARS.findall(link.get('title', ''))
    return date(int(max(years)), 12, 31) if years else None


def select_review_links(search_results: dict, company_name: str, today: date = None) -> list:
    """Fill SLOTS in order, one link each. A URL is used at most once."""
    oldest = (today or date.today()) - MAX_NEWS_AGE
    used_urls = set()
    ordered = []
    for category_key, pattern in SLOTS:
        topic = re.compile(pattern, re.I)
        for link in search_results.get(category_key, []):
            url = link.get('url', '')
            if not url or url in used_urls:
                continue
            if not topic.search(f"{link.get('title', '')} {url}"):
                continue
            if category_key in EXCLUDE and EXCLUDE[category_key].search(link.get('title', '')):
                continue
            if category_key in EXCLUDE_URL and EXCLUDE_URL[category_key].search(url):
                continue
            if not _should_include_link(link, company_name, strict=category_key in STRICT_NAME_SLOTS):
                continue
            published = _published(link) if category_key in NEWS_CATEGORIES else None
            if published and published < oldest:
                continue
            used_urls.add(url)
            ordered.append({**link,
                            'category': format_review_category_name(category_key),
                            'category_key': category_key})
            break
        else:
            logger.info(f"[{category_key}] no qualifying link")
    return ordered


def _demo():
    """Self-check: slot order, topic + company filters. Run: python -m app.utils.review_link_selection"""
    results = {
        'news_business': [{'url': 'https://x.com/a', 'title': 'Delta stock price today'},       # off-topic
                          {'url': 'https://reuters.com/b', 'title': 'Delta announces restructuring'}],
        'financials': [{'url': 'https://cnbc.com/c', 'title': 'Delta Q3 earnings beat estimates'}],
        'leadership': [{'url': 'https://reuters.com/d', 'title': 'United names new CEO'},        # wrong company
                       {'url': 'https://ir.delta.com/e', 'title': 'Delta appoints new CFO as chief financial officer'}],
        'culture': [{'url': 'https://www.comparably.com/companies/delta/culture', 'title': 'Delta Culture | Comparably'}],
        'work_life': [],                                                                       # dropped
        'diversity': [{'url': 'https://www.comparably.com/companies/delta/diversity', 'title': 'Delta Diversity'}],
        'career': [{'url': 'https://www.glassdoor.com/f', 'title': 'Delta career development reviews'}],
        'tuition': [{'url': 'https://www.glassdoor.com/g', 'title': 'Delta Tuition Assistance'}],
    }
    links = select_review_links(results, 'Delta')
    keys = [l['category_key'] for l in links]
    assert keys == ['news_business', 'financials', 'leadership', 'culture', 'diversity', 'career', 'tuition'], keys
    assert links[0]['url'] == 'https://reuters.com/b' and links[2]['url'] == 'https://ir.delta.com/e'

    # News slots need the specific name; directories and org charts aren't news
    jones = select_review_links({
        'news_business': [{'url': 'https://t.com/1', 'title': 'List of 5 Acquisitions by Jones Day'},
                          {'url': 'https://m.com/2', 'title': 'Dow Jones is cutting staff in restructuring'},
                          {'url': 'https://law.com/3', 'title': 'Jones Day restructures London office'}],
        'leadership': [{'url': 'https://c.com/4', 'title': 'Jones Day Org Chart: Leadership Team'},
                       {'url': 'https://b.com/5', 'title': 'Jones Day Names 33 New Partners'}],
    }, 'Jones Day')
    assert [l['url'] for l in jones] == ['https://law.com/3', 'https://b.com/5'], jones

    # Old news is skipped, whether dated by URL or title; undated news stays
    stale = select_review_links({
        'leadership': [{'url': 'https://wapo.com/business/2020/03/16/x', 'title': 'Delta CEO to step down'},
                       {'url': 'https://e.com/news/2025/0402_x', 'title': 'Delta CEO steps down'},
                       {'url': 'https://s.com/b', 'title': 'Delta names new CFO (2023)'},
                       {'url': 'https://x.com/news/2026/c', 'title': 'Delta names new CFO'}],
        'financials': [{'url': 'https://y.com/d', 'title': 'Delta revenue 1991-2026'}],
    }, 'Delta', today=date(2026, 10, 30))
    assert [l['url'] for l in stale] == ['https://y.com/d', 'https://x.com/news/2026/c'], stale
    print("ok:", keys)


if __name__ == "__main__":
    _demo()
