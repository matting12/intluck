# ADR 0001: Stack for the rebuild

Status: Proposed · Date: 2026-11-13

## Context

InterviewLuck is a FastAPI backend (~4,500 lines of Python) with a hand-written
frontend: one HTML file, one 1,466-line script, Tailwind loaded from a CDN at runtime.
There is no database and the cache is switched off.

The value is in the link-selection rules, tuned company by company and protected by a
41-company snapshot suite.

What we want: speed close to a plain web search; a design that holds up on phones; a
look that is ours rather than stock; AI features; and, later, accounts, saved
searches, analytics and possibly ads — without building for those before they exist.

## Decision

| Layer | Choice |
|---|---|
| Backend and all AI calls | Keep Python + FastAPI; add Pydantic response models |
| Frontend | Astro with TypeScript; React only inside interactive islands |
| Styling | Plain CSS, scoped per component, using `docs/DESIGN_TOKENS.md`. No Tailwind or other CSS framework |
| Interactive widgets | React Aria Components (behaviour and accessibility, no styling) |
| Data | One Postgres database on Railway: search cache now, users and saved searches later |
| Hosting | Railway; Astro output served as static files |
| Accounts (deferred) | Hosted sign-in (Google + email link); FastAPI verifies the session. No passwords stored by us |
| Analytics (deferred) | PostHog for product behaviour; GA4 only when ads require it; both behind consent |

## Why

- **Keep Python.** Rewriting the selection rules in another language discards the
  regression suite that keeps them correct, for no user-visible gain.
- **Astro.** The results page is mostly links. Astro sends HTML and CSS with no
  JavaScript unless a component asks for it, which is the shortest route to the
  speed target, and still lets us use React where interaction is real.
- **Plain CSS.** The stock look comes from framework defaults. Owning a small token
  set is what makes the site look like itself; modern CSS no longer needs a framework
  for layout, theming or fluid type.
- **Postgres once.** Accounts will need it, so the cache goes there too rather than
  adding a second store now and migrating later.
- **Speed is mostly backend.** Each search runs dozens of web queries, link checks
  and an LLM call. Caching and precomputing matter far more than the UI framework.

## Alternatives considered

- **Next.js.** Better if the signed-in product becomes the main thing. Rejected for
  now: more JavaScript on every page, a second server, and caching rules of its own.
- **SvelteKit.** Smallest output; smaller ecosystem for the account features.
- **Server templates + HTMX.** Least code and one service. Rejected because
  accessible widgets and account UI are easier with a component ecosystem.
- **Full rewrite in TypeScript.** Rejected: loses the selection logic and its tests.
- **Keep Tailwind, compiled properly.** Fixes the performance problem but not the
  look-and-feel goal.

## Consequences

- Two languages and two build steps (Python, Node at build time only).
- Signed-in state is fetched by islands after load; if per-user pages become
  central, revisit Next.js or Astro server rendering.
- Search-engine landing pages per company are possible later by prerendering from
  the precomputed list.
- Every visual value must exist in the tokens file; more discipline, less speed of
  throwing a page together.

## Revisit when

Accounts ship; ads are approved; the cache hit rate stays under 80%; or more than a
third of the page becomes interactive.
