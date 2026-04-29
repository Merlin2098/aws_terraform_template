# Python Project Guidance

Use straightforward Python modules with explicit inputs and outputs. Keep runtime behavior independent from generated `.ai/` artifacts, and prefer small functions that can be tested without cloud credentials.

For this repository:

- Keep pipeline logic in `src/`
- Keep orchestration visible in `main.py` or `scripts/`
- Keep SQL separate from Python and load it from files rather than embedding it in code
- Keep config and contract paths explicit in job plans and loaders
- Prefer simple modules over framework-heavy abstractions

For data and automation work, keep orchestration visible in scripts or pipeline entrypoints. Use the project virtual environment for local execution.
