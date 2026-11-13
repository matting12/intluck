# Performance budget

Goal: feel at least 70% as fast as a Brave search. All targets are proposals until
the baseline below is filled in.

## Baseline (fill in first — nothing here is measured yet)

Run the 41 companies in `docs/TEST_COMPANIES.md` cold and record from the existing
server timing logs ("Total company_info took …", etc.):

| | Median | 90th percentile |
|---|---|---|
| Box 1 total (and its GPT portion) | | |
| Box 2 total | | |
| Box 3 total | | |
| Box 4 total | | |
| Brave: one query, same network | | |
| Brave: time until results are visible in a browser | | |
| Current page: time until anything is shown | | |

## What one uncached search costs today

- Roughly 9 + 8 + 8 searches for boxes 2–4, more for box 1, all sent at once.
- A rate-limited search (HTTP 429) retries after a 1–4 s wait.
- Boxes 2–4 then check each link is alive (up to 2 s).
- Box 1 then waits for GPT.
- The page shows nothing until all four boxes have answered.

So "as fast as Brave" is reachable for searches we have seen before, and for the
first box of a new search — not for all four boxes of a never-seen company.

## Targets

Measured on a mid-range Android phone on 4G (Lighthouse mobile profile).

| Situation | Target |
|---|---|
| Page shell (form usable) | LCP ≤ 1.5 s |
| Known company (cached or precomputed): first box | ≤ 0.5 s after submit |
| Known company: all four boxes | ≤ 1.0 s |
| New company: first box | ≤ 1.5 s |
| New company: boxes 2–4 | ≤ 3 s |
| New company: box 1 | ≤ 5 s until the LLM is out of the request path, then ≤ 3 s |
| API response from cache | ≤ 100 ms server time |
| Share of searches served from cache/precompute | ≥ 80% |

Page weight and responsiveness:

| | Budget |
|---|---|
| JavaScript on the results page | ≤ 60 KB gzipped (islands only) |
| CSS | ≤ 15 KB gzipped |
| Fonts | ≤ 2 files, ≤ 80 KB, `font-display: swap` |
| Requests before first paint | ≤ 6, none to third parties |
| INP | ≤ 200 ms |
| CLS | ≤ 0.1 (ad slots reserve their size) |
| Lighthouse mobile | Performance ≥ 90, Accessibility ≥ 95 |

## How we get there, in order of payoff

1. Show each box when its own request returns (remove `Promise.all`).
2. Cache search responses.
3. Precompute the known company lists nightly.
4. Check links when the cache is written, not on each request.
5. Take the LLM out of box 1's request path.
6. Ship static HTML/CSS; drop the Tailwind CDN script.

## Rules

- Analytics and ads load after the boxes render and are not counted above, but must
  not push INP or CLS over budget.
- A change that touches the request path reports timing before and after in its PR.
- Missing a target is a bug, not a note.

## To settle

- Which Brave number is the comparison: API response time or visible results?
- Cache life per box (today's intent: box 1 one hour, box 2 seven days, boxes 3–4
  one day) versus what Brave's terms allow storing.
