from __future__ import annotations

# This hook now delegates to the agents_framework package.
# Install the package first:  pip install -e .
# Then this pre-commit hook calls the CLI entry-point.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Re-export symbols used by existing tests for backward compatibility.
from agents_framework.tools.sync_deps import (  # noqa: F401, E402
    dependencies_hash,
    dependency_files,
    main,
)

try:
    import subprocess  # noqa: F401 (also referenced by tests)
except ImportError:
    pass


def uv_command_prefix() -> list[str]:
    """Kept for test monkeypatching; now a no-op wrapper."""
    import shutil, sys as _sys
    if shutil.which("uv"):
        return ["uv"]
    if _sys.platform.startswith("win") and shutil.which("py"):
        return ["py", "-3", "-m", "uv"]
    return [_sys.executable, "-m", "uv"]


if __name__ == "__main__":
    main()
