"""
Snapshot regression tests for company overview boxes 2-4.

Every external call the endpoints make (Brave searches, domain lookup, dead-link
checks, YouTube channel verification) is recorded once per company, then replayed
offline, so the same recording always gives the same links. A changed snapshot
therefore means the code changed, not the search results.

    python -m tests.regression.run record [company ...]   # live: hits Brave/YouTube/OpenAI
    python -m tests.regression.run check  [company ...]   # offline: compare against snapshots
    python -m tests.regression.run approve [company ...]  # offline: accept current output

Box 1 (interview prep) is excluded: it still uses GPT to pick links, so its
output isn't deterministic.
"""

import asyncio
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import BackgroundTasks  # noqa: E402
import app.api.routes_company as routes  # noqa: E402
import app.utils.company_link_selection as company_selection  # noqa: E402
from app.utils.company_link_selection import PRIORITY_ORDER as BOX2_ORDER  # noqa: E402
from app.utils.salary_link_selection import SLOTS as BOX3_SLOTS  # noqa: E402
from app.utils.review_link_selection import SLOTS as BOX4_SLOTS  # noqa: E402
from tests.regression.companies import ALL, JOB_TITLES  # noqa: E402

HERE = Path(__file__).parent
RECORDINGS = HERE / 'recordings'
SNAPSHOTS = HERE / 'snapshots'

BOX_ORDER = {
    'box2': BOX2_ORDER + ['additional'],
    'box3': [key for key, *_ in BOX3_SLOTS],
    'box4': [key for key, _ in BOX4_SLOTS],
}


def slug(company: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', company.lower()).strip('-')


# The real external calls, captured before any patching
REAL = (routes.brave_search, routes.identify_company_domain,
        routes.filter_dead_links, company_selection.resolve_youtube_channel_to_video)


def _brave_key(query, category, freshness):
    return f'{category}|{freshness or ""}|{query}'


class Recorder:
    """Wraps the real external calls and stores what they returned."""

    def __init__(self):
        self.data = {'brave': {}, 'domains': {}, 'dead_urls': [], 'youtube': {}}

    async def brave_search(self, query, api_key, category=None, freshness=None):
        for attempt in range(3):
            try:
                results = await REAL[0](query, api_key, category, freshness=freshness)
                break
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 * (attempt + 1))  # rate limits: back off and retry
        self.data['brave'][_brave_key(query, category, freshness)] = results
        return results

    async def identify_company_domain(self, company, api_key):
        domain = await REAL[1](company, api_key)
        self.data['domains'][company] = domain
        return domain

    async def filter_dead_links(self, links):
        live = await REAL[2](links)
        live_urls = {l.get('url') for l in live}
        self.data['dead_urls'] += [l.get('url') for l in links if l.get('url') not in live_urls]
        return live

    async def resolve_youtube(self, link, company_name=None):
        resolved = await REAL[3](link, company_name=company_name)
        self.data['youtube'][link.get('url', '')] = resolved
        return resolved


class Replayer:
    """Serves recorded responses; anything not recorded is reported as a miss."""

    def __init__(self, data):
        self.data = data
        self.misses = []

    async def brave_search(self, query, api_key, category=None, freshness=None):
        key = _brave_key(query, category, freshness)
        if key not in self.data['brave']:
            self.misses.append(f'search not recorded: {key}')
            raise KeyError(key)
        return self.data['brave'][key]

    async def identify_company_domain(self, company, api_key):
        if company not in self.data['domains']:
            self.misses.append(f'domain lookup not recorded: {company}')
        return self.data['domains'].get(company)

    async def filter_dead_links(self, links):
        dead = set(self.data['dead_urls'])
        return [l for l in links if l.get('url') not in dead]

    async def resolve_youtube(self, link, company_name=None):
        url = link.get('url', '')
        if url not in self.data['youtube']:
            self.misses.append(f'YouTube check not recorded: {url}')
            return None
        return self.data['youtube'][url]


def _patch(brave_search, identify_company_domain, filter_dead_links, resolve_youtube):
    routes.brave_search = brave_search
    routes.identify_company_domain = identify_company_domain
    routes.filter_dead_links = filter_dead_links
    company_selection.resolve_youtube_channel_to_video = resolve_youtube


def _patch_fake(fake):
    _patch(fake.brave_search, fake.identify_company_domain, fake.filter_dead_links, fake.resolve_youtube)


async def run_boxes(company: str, job_title: str) -> dict:
    """Call the real endpoints (with whatever external calls are patched in)."""
    box2 = await routes.get_company_info(company=company, job_title=job_title,
                                         background_tasks=BackgroundTasks(), no_cache=True)
    box3 = await routes.get_salary_benefits(company=company, job_title=job_title, no_cache=True)
    box4 = await routes.get_company_reviews(company=company, no_cache=True)
    return {name: [{'slot': l.get('category_key'), 'url': l.get('url'), 'title': l.get('title')}
                   for l in box.get('links', [])]
            for name, box in (('box2', box2), ('box3', box3), ('box4', box4))}


def invariant_errors(boxes: dict) -> list:
    """Properties that must hold no matter what the search returned."""
    errors = []
    for box, links in boxes.items():
        urls = [l['url'] for l in links]
        for dup in {u for u in urls if urls.count(u) > 1}:
            errors.append(f'{box}: duplicate link {dup}')
        positions = [BOX_ORDER[box].index(l['slot']) if l['slot'] in BOX_ORDER[box] else -1 for l in links]
        if -1 in positions:
            errors.append(f'{box}: unknown slot in {[l["slot"] for l in links]}')
        elif positions != sorted(positions):
            errors.append(f'{box}: slots out of order: {[l["slot"] for l in links]}')
    return errors


def diff(expected: dict, actual: dict) -> list:
    lines = []
    for box in sorted(set(expected) | set(actual)):
        old = [(l['slot'], l['url']) for l in expected.get(box, [])]
        new = [(l['slot'], l['url']) for l in actual.get(box, [])]
        if old == new:
            continue
        lines.append(f'  {box}:')
        lines += [f'    - {s:<20} {u}' for s, u in old if (s, u) not in new]
        lines += [f'    + {s:<20} {u}' for s, u in new if (s, u) not in old]
        if sorted(old) == sorted(new):
            lines.append('    (same links, different order)')
    return lines


def _write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def _read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


async def record(company, group):
    recorder = Recorder()
    _patch_fake(recorder)
    try:
        boxes = await run_boxes(company, JOB_TITLES[group])
    finally:
        _patch(*REAL)
    _write(RECORDINGS / f'{slug(company)}.json',
           {'company': company, 'group': group, 'job_title': JOB_TITLES[group],
            'recorded_on': date.today().isoformat(), **recorder.data})
    snap_path = SNAPSHOTS / f'{slug(company)}.json'
    if not snap_path.exists():  # first recording; later ones go through check -> approve
        _write(snap_path, boxes)
    print(f'recorded {company}: ' + ', '.join(f'{b} {len(l)} links' for b, l in boxes.items()))


async def replay(company, group):
    """Returns (boxes, problems)."""
    path = RECORDINGS / f'{slug(company)}.json'
    if not path.exists():
        return None, [f'no recording — run: python -m tests.regression.run record "{company}"']
    replayer = Replayer(_read(path))
    _patch_fake(replayer)
    boxes = await run_boxes(company, JOB_TITLES[group])
    problems = invariant_errors(boxes)
    if replayer.misses:
        problems.append(f'{len(replayer.misses)} external call(s) not in the recording (queries changed?) — '
                        f're-record this company. First: {replayer.misses[0]}')
    return boxes, problems


async def main(cmd, names):
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('app').setLevel(logging.ERROR)  # replay misses are logged as errors; we report them ourselves
    companies = [(n, g) for n, g in ALL if not names or n in names]
    unknown = set(names) - {n for n, _ in companies}
    if unknown:
        sys.exit(f'Unknown company: {", ".join(unknown)}. See tests/regression/companies.py')

    if cmd == 'record':
        for company, group in companies:
            await record(company, group)
        return

    failed = 0
    for company, group in companies:
        boxes, problems = await replay(company, group)
        snap_path = SNAPSHOTS / f'{slug(company)}.json'
        if cmd == 'approve' and boxes is not None and not problems:
            _write(snap_path, boxes)
            print(f'approved {company}')
            continue
        if boxes is not None and not snap_path.exists():
            problems.append('no snapshot — review the output, then run approve')
        changes = diff(_read(snap_path), boxes) if boxes is not None and snap_path.exists() else []
        if problems or changes:
            failed += 1
            print(f'FAIL {company}')
            for p in problems:
                print(f'  ! {p}')
            print('\n'.join(changes))
        elif cmd == 'check':
            print(f'ok   {company}')
    if failed:
        print(f'\n{failed} of {len(companies)} companies failed. If the changes are intended, '
              f'run: python -m tests.regression.run approve')
        sys.exit(1)
    print(f'\nall {len(companies)} companies match their snapshots')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('record', 'check', 'approve'):
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
