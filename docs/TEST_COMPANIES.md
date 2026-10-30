# Regression Test Companies

The 41 companies below are the fixed set to check whenever link selection changes
(boxes 1–4), so a fix for one company doesn't quietly break another. They're listed in
code in `tests/regression/companies.py`, and checked by the snapshot tests in
`tests/regression/run.py` (see CLAUDE.md).

Source: the [company sheet](https://docs.google.com/spreadsheets/d/1M-vJvilBPx0sHrCg2h_iC3MDS7C6QyLj/edit)
(tabs: `Fortune 1000`, `Law Firms`, `Defense`). Names below are spelled exactly as in the
sheet, since that's what users will type or pick.

Expected domains are filled in from public knowledge, **not** the sheet. Verify each one
before turning it into a test assertion.

## Public: top 10 by revenue (Fortune 500, 2025)

| # | Company | Expected domain | Why it's a useful test |
|---|---|---|---|
| 1 | Walmart | walmart.com | Baseline |
| 2 | Amazon | amazon.com (careers: amazon.jobs) | Generic word (rainforest); careers on a separate domain |
| 3 | UnitedHealth Group | unitedhealthgroup.com | Most brand content is under subsidiaries (Optum, UnitedHealthcare) |
| 4 | Apple | apple.com | Generic word (fruit) |
| 5 | CVS Health | cvshealth.com | Corporate site vs. consumer cvs.com |
| 6 | Berkshire Hathaway | berkshirehathaway.com | Conglomerate with almost no central careers/benefits/culture pages |
| 7 | Alphabet | abc.xyz | Employer brand is Google (google.com, careers.google.com) |
| 8 | Exxon Mobil | exxonmobil.com | Spelled "ExxonMobil" in most sources |
| 9 | McKesson | mckesson.com | Baseline |
| 10 | Cencora | cencora.com | Renamed from AmerisourceBergen in 2023; older results use the old name |

## Private: top 10 by revenue (Forbes America's Largest Private Companies)

Private companies have no quarterly earnings or investor-relations pages, though a few
(e.g. Cargill) publish annual results. The box 4 "Financial Performance" slot and the
box 2 investor slot should show the company's own results or nothing, never another
company's data.

| # | Company | Expected domain | Why it's a useful test |
|---|---|---|---|
| 1 | Cargill | cargill.com | Baseline private company |
| 2 | Koch | koch.com (formerly kochind.com) | Generic surname; Koch Foods is a different company on the same list |
| 3 | Publix Super Markets | publix.com | Sheet name differs from brand name |
| 4 | Mars | mars.com | Generic word (planet) |
| 5 | H-E-B Grocery Company | heb.com | Hyphens in the name |
| 6 | Reyes Holdings | reyesholdings.com | Low public profile, so expect sparse results |
| 7 | Enterprise Mobility | enterprisemobility.com | Generic word; formerly Enterprise Holdings |
| 8 | Fidelity Investments | fidelity.com | Generic word; Fidelity National Financial is a different public company in the sheet |
| 9 | Southern Glazer's Wine & Spirits | southernglazers.com | Apostrophe and ampersand in the name |
| 10 | Cox Enterprises | coxenterprises.com | Parent of Cox Communications / Cox Automotive |

## Law firms: top 10 by revenue (Am Law 100, approximate)

The ranking is approximate. DLA Piper and Baker McKenzie would normally make the top 10 but
aren't on the `Law Firms` tab, so they're skipped. Law firms are private partnerships:
no earnings, rarely a public benefits page, and reviews are mostly on Vault, Chambers, and
Above the Law rather than Glassdoor.

| # | Company | Expected domain | Why it's a useful test |
|---|---|---|---|
| 1 | Kirkland & Ellis | kirkland.com | Ampersand in the name |
| 2 | Latham & Watkins | lw.com | Domain doesn't contain the name |
| 3 | Skadden Arps Slate Meagher & Flom | skadden.com | Long formal name; commonly called just "Skadden" |
| 4 | Sidley Austin | sidley.com | "Austin" also matches the city |
| 5 | Gibson Dunn & Crutcher | gibsondunn.com | Commonly called "Gibson Dunn" |
| 6 | Morgan Lewis & Bockius | morganlewis.com | "Morgan" also matches Morgan Stanley / JPMorgan |
| 7 | White & Case | whitecase.com | Both words are generic |
| 8 | Ropes & Gray | ropesgray.com | Both words are generic |
| 9 | Jones Day | jonesday.com | Both words are generic |
| 10 | Paul Weiss Rifkind Wharton & Garrison | paulweiss.com | Long formal name; commonly called "Paul, Weiss" |

## Defense: top 10 (order of the sheet's `Defense` tab)

| # | Company | Expected domain | Why it's a useful test |
|---|---|---|---|
| 1 | Lockheed Martin | lockheedmartin.com | Baseline |
| 2 | RTX | rtx.com | 3-letter name; renamed from Raytheon Technologies in 2023 |
| 3 | Northrop Grumman | northropgrumman.com | Baseline |
| 4 | General Dynamics | gd.com | Generic words; short domain |
| 5 | The Boeing Company | boeing.com | Leading "The" in the name |
| 6 | L3Harris Technologies | l3harris.com | Digit in the name |
| 7 | Leidos | leidos.com | Baseline |
| 8 | HII | hii.com | 3-letter name; formerly Huntington Ingalls Industries |
| 9 | Amentum | amentum.com | Formed by a 2024 merger, so its history is short and results are sparse |
| 10 | Booz Allen Hamilton | boozallen.com | Sheet's Fortune tab lists it as "Booz Allen Hamilton Holding" |

## Notes on the sheet itself

- **The `Website` column is shifted down by one row in the private-company block** (starting at
  Cargill, whose row shows supermicrocomputer.com). Don't use the sheet's websites as ground truth.
- The `Fortune 1000` tab isn't in rank order. It holds the Fortune 1000 (rows 2–1001), then
  the Forbes private list (Cargill onward, about 200 rows), then about 100 extra public mid-caps.
- The `Law Firms` tab has 407 rows but only 145 unique firms, so it contains duplicates.
- The `ISD` tab is empty.

## Past production bugs

Companies that broke in production before. Keep them covered so the same bug can't return.

| Company | Expected domain | What broke |
|---|---|---|
| Delta Air Lines | delta.com | Domain detection drifted to a booking/service page; "Delta" alone is ambiguous (Delta Dental, Delta Faucet); box 4 ordering |
