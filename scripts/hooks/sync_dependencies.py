from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ai.runtime.profile import resolve_environment_profile  # noqa: E402


HASH_FILE = Path(".venv/.deps_hash")
ENVIRONMENT_PROFILES = {"local", "cloud"}
PROFILE_FILE = Path(".template-profile")


def dependency_files() -> tuple[Path, ...]:
    files = [Path("pyproject.toml")]
    lock_file = Path("uv.lock")
    if lock_file.exists():
        files.append(lock_file)
    if PROFILE_FILE.exists():
        files.append(PROFILE_FILE)
    return tuple(path for path in files if path.exists())


def dependencies_hash(paths: tuple[Path, ...], profile: str) -> str:
    digest = hashlib.md5()
    digest.update(profile.encode("utf-8"))
    for dependency_path in paths:
        if not dependency_path.exists():
            continue
        digest.update(str(dependency_path.resolve()).encode("utf-8"))
        digest.update(dependency_path.read_bytes())
    return digest.hexdigest()


def uv_command_prefix() -> list[str]:
    if shutil.which("uv"):
        return ["uv"]
    if sys.platform.startswith("win") and shutil.which("py"):
        return ["py", "-3", "-m", "uv"]
    return [str(sys.executable), "-m", "uv"]


def install_command(profile: str) -> list[str]:
    command = uv_command_prefix() + ["sync"]
    if profile == "cloud":
        command.extend(["--extra", "local", "--extra", "cloud"])
    command.extend(["--group", "dev-local"])
    if profile == "cloud":
        command.extend(["--group", "dev-cloud"])
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize host project dependencies."
    )
    parser.add_argument("--profile", choices=sorted(ENVIRONMENT_PROFILES))
    return parser.parse_args()


def resolve_profile(selected: str | None) -> str:
    if selected:
        return selected
    return resolve_environment_profile(PROFILE_FILE, None)


def main() -> None:
    args = parse_args()
    profile = resolve_profile(args.profile)
    paths = dependency_files()
    if not paths:
        return

    current_hash = dependencies_hash(paths, profile)
    if HASH_FILE.exists() and HASH_FILE.read_text() == current_hash:
        print("Dependencies unchanged. Skipping install.")
        return

    print("Installing dependencies...")
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(install_command(profile), check=True)
    HASH_FILE.write_text(current_hash)
    print("Dependencies updated.")


if __name__ == "__main__":
    main()
