from __future__ import annotations

import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    command = [sys.executable, "-m", "pytest", *(argv or sys.argv[1:])]
    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
