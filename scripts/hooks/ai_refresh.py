from __future__ import annotations

# This hook now delegates to the agents_framework package.
# Install the package first:  pip install -e .
# Then this pre-commit hook calls the CLI entry-point.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    from agents_framework.tools.refresh_context import main
    raise SystemExit(main())
