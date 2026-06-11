from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.runtime.profile import PROFILE_FILENAME  # noqa: E402
from ai.runtime.project_profile import (  # noqa: E402
    resolve_project_profile,
    uv_sync_args,
)


HASH_FILE = Path(".venv/.deps_hash")


def dependency_files() -> tuple[Path, ...]:
    files = [
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path(PROFILE_FILENAME),
    ]
    files.extend(sorted(Path("ai/capabilities").glob("*/*.yaml")))
    return tuple(path for path in files if path.exists())


def dependencies_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.md5()
    for dependency_path in paths:
        digest.update(str(dependency_path.resolve()).encode("utf-8"))
        digest.update(dependency_path.read_bytes())
    return digest.hexdigest()


def uv_command_prefix() -> list[str]:
    if shutil.which("uv"):
        return ["uv"]
    if sys.platform.startswith("win") and shutil.which("py"):
        return ["py", "-3", "-m", "uv"]
    return [str(sys.executable), "-m", "uv"]


def install_command() -> list[str]:
    resolved = resolve_project_profile(Path.cwd())
    return uv_command_prefix() + uv_sync_args(resolved)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize capability-aware host dependencies."
    )
    parser.parse_args()
    return argparse.Namespace()


def main() -> None:
    parse_args()
    paths = dependency_files()
    if not paths:
        return

    current_hash = dependencies_hash(paths)
    if HASH_FILE.exists() and HASH_FILE.read_text(encoding="utf-8") == current_hash:
        print("Dependencies unchanged. Skipping install.")
        return

    print("Installing dependencies...")
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(install_command(), check=True)
    HASH_FILE.write_text(current_hash, encoding="utf-8")
    print("Dependencies updated.")


if __name__ == "__main__":
    main()
