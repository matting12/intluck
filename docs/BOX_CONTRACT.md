# Box contract

What each results box takes, returns and guarantees. This describes current behaviour
(branch `box4-three-per-slot`). The frontend may rely on anything here; changing it
means updating this file and the regression snapshots together.

## Shared rules

- **Inputs** come from one search form: company (required), job title (required),
  and location as either Remote or any of state / city / zip.
- **Location resolution**, first match wins: Remote → "Remote"; city + state →
  "City, ST"; state → state; zip → zip; city → city; nothing → "Remote".
- **Link object** (boxes 2–4): `url`, `title` (formatted as "Page Title | Site Name"),
  `description`, and `category` — the section heading as display text (e.g.
  "Salary Information", "Apple Recent News"). Box 3 also sends `category_key`.
  Video links add `type: "video"` so the frontend can embed them.
  Regression snapshots record only `slot`, `url` and `title` per link, so
  `description` and `type` are not regression-protected.
  (Box 1's link fields come from the GPT/scoring path and are not listed here yet.)
- **Every response** has `links` (what to show), `all_links`, and `total_found`.
- **No fillers.** A section with no qualifying link is omitted, not padded.
  Frontend text for an empty section today: "No high-quality results found for
  this category".
- **Dead links**: boxes 2–4 drop links that return 404/410 or fail DNS/connect
  (HEAD request, 2 s timeout; timeouts are kept). Box 1 does not check.
- **Ordering is part of the contract.** Sections and links appear in the order listed.
- **Independence (target, not true today)**: each box loads, fails and shows its
  empty state on its own. Today the page waits for all four and hides everything if
  one fails.

## Box 1 — Interview preparation  `GET /api/interview-prep`

| | |
|---|---|
| Inputs | `company`, `job_title`, `max_links` (default 6) |
| Uses location | No |
| Max links | 6, plus up to 3 "inspirational posts" |
| Sections | Company Interview Questions · Tech Stack & Tools · Technical Skills · General Prep |
| Selection | Job family inferred from title → family-specific searches → drop blacklisted URLs → keep only titles containing the company name → max 1 link per domain → **GPT picks** → keep links scoring ≥ 45 |
| Inspirational posts | LinkedIn Pulse and Medium "how I got hired" posts; company must appear in URL, title or description; first 3 |
| Extra fields | `job_family`, `threshold`, `inspirational_posts`; `all_links` is every scored candidate (feeds the "more links" modal) |
| Freshness | None |
| Intended cache life | 1 hour |
| Deterministic | **No** (GPT). Not covered by regression snapshots. |
| Empty state | `links: []`; inspirational posts may still be present |

## Box 2 — Company information  `GET /api/company-info`

| | |
|---|---|
| Inputs | `company`, `job_title`, location fields, `max_links` (default 9), `no_cache` |
| Uses location | Accepted and part of the cache key; job title drives the role-specific slot |
| Max links | 9 |
| Sections, in order, 1 link each | Company Website · About & Mission · Official Social Media · YouTube · Community Engagement · Recent News · Investor Relations · Role-Specific Page |
| Overflow | Remaining room up to 9 is filled with "Additional Links" from the company's own pages |
| Sources | Company's own domain only, except Social (verified profiles) and YouTube (official channel, resolved to a featured video). With no verified channel, the YouTube slot can hold a second "Official Social Media" link instead |
| Domain lookup | Manual override → known-company database → inferred from search |
| Freshness | None |
| Intended cache life | 7 days |
| Deterministic | Yes. Snapshot-tested. |
| Empty / error state | If the domain can't be identified: `domain: null`, `links: []`, `error: "Could not identify company domain"` |
| Side effect | An unknown company triggers background enrichment into the company database |

## Box 3 — Salary and benefits  `GET /api/salary-benefits`

| | |
|---|---|
| Inputs | `company`, `job_title`, location fields, `no_cache` |
| Uses location | Yes (salary queries are location-specific) |
| Max links | 9 |
| Sections, in order (max links) | Company Benefits & Total Rewards (1) · Salary Information (2) · Negotiating Salary (2: company-specific first, then job-title advice) · Benefits & Perks Reviews (2) · Benefits Video (1) · Industry Benefits Comparison (1) |
| Rules | One link per domain within a section (except video). Open-web results need the full company name; review sites accept the short name. Job postings excluded. |
| Domain lookup | Manual override → inferred from search → falls back to `<company>.com` |
| Freshness | None |
| Intended cache life | 1 day |
| Deterministic | Yes. Snapshot-tested. |
| Empty state | Sections with nothing are omitted; `links` may be `[]` |
| Extra fields | Echoes `company`, `job_title`, `location` |

## Box 4 — News and reviews  `GET /api/company-reviews`

| | |
|---|---|
| Inputs | `company`, `no_cache` |
| Uses location | No |
| Max links | 24 (8 sections × up to 3) |
| Sections, in order | {Company} Recent News · {Company} Financial News · {Company} Executive Leadership News · Reviews on Company Culture · Reviews on Work Life Balance · Reviews on Diversity, Equity, and Inclusion · Reviews on Career Development and Internal Mobility · Reviews on Tuition Reimbursement |
| Presentation | Each section is a dropdown |
| Freshness | The three news sections only: searched with a past-year filter, then kept only if the date in the URL or title falls within the **6 calendar months** before the search |
| Rules | Title/URL must match the section topic. News, DEI and tuition need the full company name. Directory, profile, law-firm practice and job-listing pages are excluded. |
| Intended cache life | 1 day (news changes daily) |
| Deterministic | Yes, given a fixed "today". Snapshot-tested. |
| Empty state | Sections with nothing are omitted |

## Not boxes (same page, separate contracts to write later)

- `GET /api/autocomplete/job-title`, `/company`, `/company-confirm`
- `POST /api/generate-questions` (behavioural + technical questions from a job description)
- `POST /api/analyze-resume` (PDF/DOCX → matching / missing / related keywords)

## Open questions

1. Should box 1 get a dead-link check and a `no_cache` flag like the others?
2. Box 2 accepts location but does it change any result? If not, drop it from the cache key.
3. Is the empty-section message the same for every box, or should each say what to try next?
