# SQL Workflow Guidance

Keep SQL in versioned `.sql` files when queries are shared, reused, or reviewed. Prefer clear CTE names, explicit column lists, and small test fixtures for important transformations.

For this repository:

- Store reusable SQL under `src/transformations/`
- Load SQL explicitly from Python job code instead of embedding long query strings
- Keep transformation steps readable with named CTEs for extraction, cleanup, filtering, and final projection
- Make column and dataset naming consistent with the contract in `src/contracts/`
- Add targeted test coverage for important transformation assumptions when practical

When Python calls SQL, keep the file path explicit in config and resolve it close to the execution boundary.
