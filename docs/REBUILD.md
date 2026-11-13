# Rebuild guidelines for agents

Read first: `docs/adr/0001-stack.md`, `docs/BOX_CONTRACT.md`, `docs/DESIGN_TOKENS.md`,
`docs/PERF_BUDGET.md`, and `CLAUDE.md`.

## Goal
Rebuild the frontend and data layer for speed, mobile and a distinct visual identity,
without changing which links any box returns.

## Priorities, in order
1. Speed — `docs/PERF_BUDGET.md`. Missing a target means the change is not done.
2. Mobile — design at 360 px first; Core Web Vitals "good"; WCAG 2.2 AA; 44 px tap
   targets; 16 px minimum input text; nothing that needs hover.
3. Look and feel — only values from `docs/DESIGN_TOKENS.md`. No Tailwind, no CSS
   framework, no gradients, no emoji icons. A new colour, radius, shadow or font
   needs the owner's approval.

## Stack (do not substitute)
As decided in `docs/adr/0001-stack.md`.

## Hard rules
1. Selection behaviour is frozen. `python -m tests.regression.run check` must pass
   before and after every commit. An unexpected diff means stop and report; never
   `approve` to make a refactor pass.
2. Do not edit logic in `app/utils/*_link_selection.py`, `*_queries.py`,
   `link_scoring.py`, `trusted_domains.py`, `domain_overrides.py`,
   `exact_match_companies.py`. Moving a file is fine.
3. `docs/BOX_CONTRACT.md` is the interface. If code and contract disagree, stop and
   ask which is right; update both in the same PR.
4. One phase per PR; a phase starts only after the previous one is merged.
5. A page ships no JavaScript unless it contains an island. Each island says in a
   comment why it cannot be plain HTML. No client-side router, no global state library.
6. Nothing third-party blocks first paint. Analytics and ads load after consent and
   after the boxes render. Ad slots reserve fixed dimensions.
7. No new dependency without a line in the PR naming the built-in or installed
   option that was rejected and why.
8. Tests never call live APIs. Use recordings; `run fill "<company>"` only when a
   query genuinely changed.
9. Secrets from env only. Never log resume text or job descriptions. Analytics gets
   an anonymous id and event names, nothing else.
10. Do not build accounts, saved searches, ads or per-company pages until the owner
    opens that phase.

## Phases
0. **Measure** — fill in the baseline table in `docs/PERF_BUDGET.md`. No code changes.
1. **Independent boxes** — in the current frontend, render each box when its own
   request returns and give each its own error state. Done: one failing endpoint no
   longer blanks the page.
2. **Contracts** — Pydantic response models matching `docs/BOX_CONTRACT.md` and
   current JSON exactly. Done: snapshots pass; `/docs` shows typed schemas.
3. **Split `routes_company.py`** — thin routes; helpers to `app/services/`. Pure
   move. Done: snapshots pass, no function body changed.
4. **Cache** — implement `get_cached`/`set_cached` (`app/utils/cache.py`, same
   signatures and TTL constants) on a Postgres table. Cache raw search responses,
   not selected links, so rule changes apply immediately. Check links at cache-write
   time. Done: a repeat request makes no outbound calls and meets the cached target.
5. **Precompute** — nightly job warms the cache for the company lists in the repo.
6. **Tokens and shell** — tokens as CSS custom properties, base type, 360 px layout,
   dark mode. Owner approves a static mock of one results page before any box is ported.
7. **Port the boxes** — one Astro component per box, one box per PR, deleting the
   matching code from `static/js/main.js` in the same PR. Islands only for
   autocomplete, question generator, resume analyser. Done: `main.js` and the
   Tailwind CDN script are gone; page-weight budget met; keyboard-only use works.
8. **Box 1 determinism** — rules first, LLM optional and off the request path. This
   changes output: record box 1 snapshots, review diffs with the owner, then `approve`.
9. **Hardening** — remove wildcard CORS and the no-cache middleware; hashed static
   filenames instead of `?v=N`.
Later, each opened separately: analytics + consent, accounts + saved searches,
per-company pages, ads.

## Per-change checklist
- Read the code path end to end; grep callers of anything you touch.
- Run the self-check of each selection module touched (`python -m app.utils.<module>`).
- Run `python -m tests.regression.run check`.
- Frontend: check at 360 px and 1280 px, light and dark, with one exact-match
  company, one from `notes/empty-results-companies.txt`, and one with no location.
- PR description: what moved, what changed behaviour (ideally nothing), regression
  result, and timing before/after if the request path was touched.
