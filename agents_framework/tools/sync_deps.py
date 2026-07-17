from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from agents_framework.runtime.profile import PROFILE_FILENAME, PROFILE_FILENAME_LEGACY
from agents_framework.runtime.project_profile import (
    pip_install_args,
    resolve_project_profile,
    uv_sync_args,
)


HASH_FILE = Path(".venv/.deps_hash")


def dependency_files(project_root: Path | None = None) -> tuple[Path, ...]:
    root = (project_root or Path.cwd()).resolve()
    candidates = [
        root / PROFILE_FILENAME,
        root / PROFILE_FILENAME_LEGACY,
        root / "pyproject.toml",
        root / "uv.lock",
    ]
    candidates.extend(sorted((root / "agents_framework" / "capabilities").glob("*/*.yaml")))
    # Also check the framework-side capabilities in dev mode
    from agents_framework import framework_root
    capabilities_dir = framework_root() / "capabilities"
    if capabilities_dir.is_dir():
        candidates.extend(sorted(capabilities_dir.glob("*/*.yaml")))
    return tuple(p for p in candidates if p.exists())


def dependencies_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.md5()
    for dependency_path in paths:
        digest.update(str(dependency_path.resolve()).encode("utf-8"))
        digest.update(dependency_path.read_bytes())
    return digest.hexdigest()


def _manager_command_prefix(manager: str) -> list[str]:
    if manager == "uv":
        if shutil.which("uv"):
            return ["uv"]
        if sys.platform.startswith("win") and shutil.which("py"):
            return ["py", "-3", "-m", "uv"]
        return [sys.executable, "-m", "uv"]
    # pip (default)
    pip = shutil.which("pip") or shutil.which("pip3")
    if pip:
        return [pip]
    return [sys.executable, "-m", "pip"]


def install_command(project_root: Path) -> list[str]:
    resolved = resolve_project_profile(project_root)
    manager = resolved.profile.dependency_policy.manager
    prefix = _manager_command_prefix(manager)
    if manager == "uv":
        return prefix + uv_sync_args(resolved)
    return prefix + pip_install_args(resolved)


def main(project_root: Path | None = None) -> None:
    root = (project_root or Path.cwd()).resolve()
    paths = dependency_files(root)
    if not paths:
        return

    current_hash = dependencies_hash(paths)
    hash_file = root / ".venv" / ".deps_hash"
    if hash_file.exists() and hash_file.read_text(encoding="utf-8") == current_hash:
        print("Dependencies unchanged. Skipping install.")
        return

    print("Installing dependencies...")
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(install_command(root), check=True)
    hash_file.write_text(current_hash, encoding="utf-8")
    print("Dependencies updated.")


if __name__ == "__main__":
    main()
