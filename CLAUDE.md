# intluck

## Avoiding regressions in link selection

Changes to how a box picks or orders links (boxes 1–4, under `app/utils/*_queries.py`,
`app/utils/*_link_selection.py`, and the routes in `app/api/routes_company.py`) have
repeatedly fixed one company and broken another. Before shipping such a change:

1. Run the self-check for each selection module you touched, e.g.
   `python -m app.utils.salary_link_selection`.
2. Run the snapshot regression tests (offline, a few seconds):
   `python -m tests.regression.run check`
   They replay recorded search results for the 41 companies in
   [docs/TEST_COMPANIES.md](docs/TEST_COMPANIES.md) through boxes 2–4 and diff each box's
   links against the approved snapshot.
   - A diff you intended: review it, then `python -m tests.regression.run approve`.
   - "not in the recording": the change made a call that was never recorded (a changed
     search query, or a YouTube channel now being considered). Run
     `python -m tests.regression.run fill "<company>"`: it makes live calls only for what's
     missing and keeps everything else, so the next `check` diff is your change alone.
     (`record` re-records everything with fresh search results — use it to refresh a
     company, not to test a change, since its diff mixes in search drift.)
3. Box 1 (interview prep) isn't covered yet: it still uses GPT to pick links, so its
   output isn't deterministic.
