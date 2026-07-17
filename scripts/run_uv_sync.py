# Capability-aware wrapper around uv for managing the Python virtual environment.
# Reads .template-profile.yaml to determine which extras and dependency groups are
# active, then runs the appropriate uv command. Handles OneDrive symlink issues
# automatically (UV_LINK_MODE=copy) and recovers from locked .venv states.
#
# Modes:
#   init   — create or sync .venv from the current lockfile
#   update — upgrade all dependencies (uv lock --upgrade) then sync
#   reset  — delete .venv and recreate it from scratch
#   ci     — verify lockfile is up to date (uv lock --check) then sync
#
# Usage: python scripts/run_uv_sync.py <mode> [--include-dev | --no-dev] [--dry-run]
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = REPO_ROOT / ".venv"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents_framework.runtime.profile import DependencyPolicy, Profile, load_profile  # noqa: E402
from agents_framework.runtime.project_profile import (  # noqa: E402
    ResolvedProfile,
    resolve_project_profile,
    uv_sync_args,
)


def uv_command_prefix(python_path: str | None = None) -> list[str]:
    uv_path = shutil.which("uv")
    if uv_path:
        return [uv_path]
    if python_path:
        return [python_path, "-m", "uv"]
    if sys.platform.startswith("win") and shutil.which("py"):
        return ["py", "-3", "-m", "uv"]
    return [sys.executable, "-m", "uv"]


def resolve_active_profile(
    *, use_dev_dependencies: bool | None = None
) -> ResolvedProfile:
    profile = load_profile(REPO_ROOT)
    if use_dev_dependencies is not None:
        profile = Profile(
            capabilities=profile.capabilities,
            declared_capabilities=profile.declared_capabilities,
            dependency_policy=DependencyPolicy(
                include_dev=use_dev_dependencies,
                manager=profile.dependency_policy.manager,
                authority=profile.dependency_policy.authority,
                additional_extras=profile.dependency_policy.additional_extras,
                additional_groups=profile.dependency_policy.additional_groups,
            ),
            schema_version=profile.schema_version,
            source=profile.source,
        )
    return resolve_project_profile(REPO_ROOT, profile=profile)


def sync_command(
    resolved: ResolvedProfile,
    *,
    python_path: str | None = None,
    locked: bool = False,
) -> list[str]:
    return uv_command_prefix(python_path) + uv_sync_args(resolved, locked=locked)


def lock_command(python_path: str | None = None, *, check: bool = False) -> list[str]:
    return uv_command_prefix(python_path) + (
        ["lock", "--check"] if check else ["lock", "--upgrade"]
    )


def uv_environment() -> dict[str, str]:
    env = os.environ.copy()
    if "UV_LINK_MODE" not in env and "OneDrive" in str(REPO_ROOT):
        env["UV_LINK_MODE"] = "copy"
    return env


def remove_readonly(func, path, exc_info) -> None:  # pragma: no cover
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def reset_venv() -> None:
    resolved = VENV_DIR.resolve()
    if resolved == REPO_ROOT.resolve() or resolved.parent != REPO_ROOT.resolve():
        raise RuntimeError(
            f"Refusing to remove unexpected environment path: {resolved}"
        )
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, onexc=remove_readonly)


def is_permission_sync_error(error: subprocess.CalledProcessError) -> bool:
    text = f"{error.stdout or ''}{error.stderr or ''}".lower()
    return any(
        marker in text
        for marker in ("failed to remove directory", "access denied", "acceso denegado")
    )


def run(command: list[str], *, dry_run: bool) -> None:
    print(" ".join(command))
    if dry_run:
        return
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=uv_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )


def run_init(
    *,
    dry_run: bool,
    resolved: ResolvedProfile,
    python_path: str | None,
    locked: bool = False,
) -> None:
    command = sync_command(resolved, python_path=python_path, locked=locked)
    try:
        run(command, dry_run=dry_run)
    except subprocess.CalledProcessError as error:
        if dry_run or locked or not is_permission_sync_error(error):
            raise
        print(
            "uv sync hit a locked or inconsistent .venv. "
            "Rebuilding the environment and retrying..."
        )
        try:
            reset_venv()
        except OSError as reset_error:
            raise SystemExit(
                "Could not reset .venv because some files are still in use. "
                "Close editors, terminals, or background tools using the "
                "environment and run `make uv-reset`."
            ) from reset_error
        run(command, dry_run=False)


def run_update(
    *,
    dry_run: bool,
    resolved: ResolvedProfile,
    python_path: str | None,
) -> None:
    try:
        run(lock_command(python_path), dry_run=dry_run)
        run(sync_command(resolved, python_path=python_path), dry_run=dry_run)
    except subprocess.CalledProcessError as error:
        if not dry_run and is_permission_sync_error(error):
            raise SystemExit(
                "uv update could not clean the current .venv. Close tools "
                "using the environment and run `make uv-reset`."
            ) from error
        raise


def run_reset(
    *,
    dry_run: bool,
    resolved: ResolvedProfile,
    python_path: str | None,
) -> None:
    print(f"Resetting {VENV_DIR}")
    if not dry_run:
        try:
            reset_venv()
        except OSError as error:
            raise SystemExit(
                "Could not remove .venv because some files are still in use. "
                "Close tools using the environment and retry `make uv-reset`."
            ) from error
    run(sync_command(resolved, python_path=python_path), dry_run=dry_run)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run capability-aware uv environment commands."
    )
    parser.add_argument("mode", choices=("init", "update", "reset", "ci"))
    parser.add_argument(
        "--python-path",
        help="Use this Python interpreter for `python -m uv` when needed.",
    )
    dev_group = parser.add_mutually_exclusive_group()
    dev_group.add_argument("--include-dev", action="store_true")
    dev_group.add_argument("--no-dev", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.python_path and not Path(args.python_path).exists():
        raise SystemExit(f"Python not found at '{args.python_path}'.")

    dev_override = False if args.no_dev else True if args.include_dev else None
    resolved = resolve_active_profile(use_dev_dependencies=dev_override)
    if args.mode == "init":
        run_init(
            dry_run=args.dry_run,
            resolved=resolved,
            python_path=args.python_path,
        )
    elif args.mode == "update":
        run_update(
            dry_run=args.dry_run,
            resolved=resolved,
            python_path=args.python_path,
        )
    elif args.mode == "reset":
        run_reset(
            dry_run=args.dry_run,
            resolved=resolved,
            python_path=args.python_path,
        )
    else:
        run(lock_command(args.python_path, check=True), dry_run=args.dry_run)
        run_init(
            dry_run=args.dry_run,
            resolved=resolved,
            python_path=args.python_path,
            locked=True,
        )


if __name__ == "__main__":
    main()
