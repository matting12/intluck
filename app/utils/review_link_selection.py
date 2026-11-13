"""
Link selection and ordering for company news & reviews (company overview box 4).
Up to three links per slot, in strict order (see SLOTS). Each link must name the company
and have an on-topic title or URL; slots with no qualifying link are dropped.
"""

import logging
import re
from datetime import date
from urllib.parse import urlparse
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
    # Job listings ("Cargill Careers and Employment | Indeed") and sales roles aren't career-growth reviews
    'career': re.compile(r'careers and employment|business development', re.I),
}
EXCLUDE_URL = {
    'news_business': re.compile(r'/(insights?|publications?|practices?)/|client-memos', re.I),
}

# Open-web slots need the specific company name, not just its first word — otherwise
# "Jones Day" pulls in Dow Jones and "Fidelity Investments" pulls in FIS. Review-site
# slots stay lenient: those pages are company-scoped and often use the short name.
STRICT_NAME_SLOTS = {'news_business', 'financials', 'leadership', 'diversity', 'tuition'}

# Recent news = published within the six calendar months before the search. Brave's
# freshness filter can't do this (it goes by crawl date, so "Sundar Pichai named CEO"
# from 2019 comes back as past-year), so dates come from the URL or title instead.
NEWS_MONTHS = 6
LINKS_PER_SLOT = 3
URL_DATE = re.compile(r'/(20\d\d)/(?:(\d\d)(?=[/_-]|\d\d))?')  # /2020/03/16/, /2025/0402_, /2026/
TITLE_YEARS = re.compile(r'\b(20\d\d)\b')


def _months_ago(today: date, months: int) -> date:
    y, m = divmod(today.year * 12 + today.month - 1 - months, 12)
    return date(y, m + 1, 1)


def _published(link: dict):
    """
    Best guess at the month a page was published: the date in its URL, else the latest
    year in its title ("Revenue 1991-2026"). A bare year counts as that December, so
    /2026/ isn't dropped for lack of a month. None if unknown. (Brave's page_age is
    no use here: it's the last crawl/modify date, so a 2024 article reads as 2026.)
    """
    m = URL_DATE.search(link.get('url', ''))
    if m:
        month = int(m[2] or 12)
        return date(int(m[1]), month if 1 <= month <= 12 else 12, 1)  # /2026/40/ isn't a month
    years = TITLE_YEARS.findall(link.get('title', ''))
    return date(int(max(years)), 12, 1) if years else None


def _site(url: str) -> str:
    """Registered domain, so ir.delta.com and news.delta.com (the same press release twice) count as one site."""
    return '.'.join(urlparse(url).netloc.lower().split('.')[-2:])


def select_review_links(search_results: dict, company_name: str, today: date = None) -> list:
    """
    Fill SLOTS in order, up to LINKS_PER_SLOT each, from different sites. A URL is used
    at most once. News slots drop links dated before the NEWS_MONTHS window and list
    dated (recent) news ahead of undated news.
    """
    oldest = _months_ago(today or date.today(), NEWS_MONTHS)
    used_urls = set()
    ordered = []
    for category_key, pattern in SLOTS:
        topic = re.compile(pattern, re.I)
        candidates = []
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
            candidates.append((published is None and category_key in NEWS_CATEGORIES, link))
        candidates.sort(key=lambda c: c[0])  # stable: dated news first, search order kept
        sites = set()
        for _, link in candidates:
            if _site(link['url']) in sites:
                continue
            sites.add(_site(link['url']))
            used_urls.add(link['url'])
            ordered.append({**link,
                            'category': format_review_category_name(category_key, company_name),
                            'category_key': category_key})
            if len(sites) == LINKS_PER_SLOT:
                break
        if not sites:
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
    assert links[0]['category'] == 'Delta Recent News'

    # Up to three per slot, each from a different site
    culture = select_review_links({'culture': [
        {'url': f'https://www.{site}/delta/culture/{i}', 'title': 'Delta Culture Reviews'}
        for i, site in enumerate(['glassdoor.com', 'glassdoor.com', 'indeed.com', 'comparably.com', 'vault.com'])]},
        'Delta')
    assert [l['url'] for l in culture] == ['https://www.glassdoor.com/delta/culture/0', 'https://www.indeed.com/delta/culture/2',
                                           'https://www.comparably.com/delta/culture/3'], culture

    # News slots need the specific name; directories and org charts aren't news
    jones = select_review_links({
        'news_business': [{'url': 'https://t.com/1', 'title': 'List of 5 Acquisitions by Jones Day'},
                          {'url': 'https://m.com/2', 'title': 'Dow Jones is cutting staff in restructuring'},
                          {'url': 'https://law.com/3', 'title': 'Jones Day restructures London office'}],
        'leadership': [{'url': 'https://c.com/4', 'title': 'Jones Day Org Chart: Leadership Team'},
                       {'url': 'https://b.com/5', 'title': 'Jones Day Names 33 New Partners'}],
    }, 'Jones Day')
    assert [l['url'] for l in jones] == ['https://law.com/3', 'https://b.com/5'], jones

    # News from before the six calendar months is skipped, whether dated by URL or
    # title; undated news stays but comes after dated news
    assert _months_ago(date(2026, 11, 13), 6) == date(2026, 5, 1)
    assert _months_ago(date(2026, 3, 31), 6) == date(2025, 9, 1)
    stale = select_review_links({
        'leadership': [{'url': 'https://u.com/a', 'title': 'Delta names new CFO'},                  # undated
                       {'url': 'https://wapo.com/business/2020/03/16/x', 'title': 'Delta CEO to step down'},
                       {'url': 'https://e.com/news/2026/04/x', 'title': 'Delta CEO steps down'},  # April: too old
                       {'url': 'https://s.com/b', 'title': 'Delta names new CFO (2025)'},
                       {'url': 'https://m.com/news/2026/05/c', 'title': 'Delta names new COO'},
                       {'url': 'https://x.com/news/2026/c', 'title': 'Delta names new CFO'}],  # year only: kept
        'financials': [{'url': 'https://y.com/d', 'title': 'Delta revenue 1991-2026'}],
    }, 'Delta', today=date(2026, 11, 13))
    assert [l['url'] for l in stale] == ['https://y.com/d', 'https://m.com/news/2026/05/c',
                                         'https://x.com/news/2026/c', 'https://u.com/a'], stale
    print("ok:", keys)


if __name__ == "__main__":
    _demo()
