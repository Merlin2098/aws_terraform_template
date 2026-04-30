from __future__ import annotations

import subprocess
import sys
from pathlib import Path


DEFAULT_TARGETS = ("ai", "src", "tests", "scripts")


def main() -> int:
    project_root = Path.cwd()
    existing_targets = [
        target for target in DEFAULT_TARGETS if (project_root / target).exists()
    ]

    if not existing_targets:
        print("No Ruff targets found. Skipping lint.")
        return 0

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *existing_targets], check=False
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
