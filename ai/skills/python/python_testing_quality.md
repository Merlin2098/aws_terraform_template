# Python Testing And Quality

Use this guidance when adding tests, refactoring Python modules, or reviewing automation scripts.

Favor tests that explain behavior:

- Test pure transformation and planning functions separately from IO and cloud clients.
- Use fixtures or tiny sample payloads with explicit environment assumptions.
- Keep AWS calls behind small boundaries that can be stubbed or mocked.
- Validate error paths, empty inputs, malformed rows, and configuration failures.
- Keep formatting and linting boring; readability beats clever abstractions.

For this template, include at least:

- one happy-path sample for the job or transformation
- one failure sample for schema or quality checks
- explicit assertions around loaded config, SQL text, and contract structure
