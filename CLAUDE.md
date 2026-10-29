# intluck

## Avoiding regressions in link selection

Changes to how a box picks or orders links (boxes 1–4, under `app/utils/*_queries.py` and
`app/utils/*_link_selection.py`) have repeatedly fixed one company and broken another.
Before shipping such a change:

1. Run the self-check for each selection module you touched, e.g.
   `python -m app.utils.salary_link_selection`.
2. Spot-check the affected box against the regression companies in
   [docs/TEST_COMPANIES.md](docs/TEST_COMPANIES.md): 10 public, 10 private, 10 law firms, and
   10 defense companies, each chosen for a specific edge case.
