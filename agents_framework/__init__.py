from __future__ import annotations

from pathlib import Path


def framework_root() -> Path:
    """Return the directory that contains framework resources (capabilities, skills, etc.).

    Resolution order:
    1. A ``data/`` subdirectory co-located with this file — used when resources are
       bundled as package-data in the installed wheel.
    2. An ``ai/`` directory at the repository root — used during editable development
       inside the ``agents_template`` source tree.
    3. The package directory itself — fallback for unusual layouts.
    """
    pkg_dir = Path(__file__).parent

    bundled = pkg_dir / "data"
    if bundled.is_dir() and (bundled / "capabilities").is_dir():
        return bundled

    repo_root = pkg_dir.parent
    legacy = repo_root / "ai"
    if (legacy / "capabilities").is_dir():
        return legacy

    return pkg_dir
