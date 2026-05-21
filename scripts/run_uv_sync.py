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
PROFILE_FILE = REPO_ROOT / ".template-profile"
ENVIRONMENT_PROFILES = {"local", "cloud"}


def uv_command_prefix(python_path: str | None = None) -> list[str]:
    uv_path = shutil.which("uv")
    if uv_path:
        return [uv_path]
    if python_path:
        return [python_path, "-m", "uv"]
    if sys.platform.startswith("win") and shutil.which("py"):
        return ["py", "-3", "-m", "uv"]
    return [sys.executable, "-m", "uv"]


def profile_from_template_file() -> str | None:
    if not PROFILE_FILE.exists():
        return None
    for line in PROFILE_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator and key.strip() == "environment_profile":
            normalized = value.strip().lower()
            if normalized in ENVIRONMENT_PROFILES:
                return normalized
    return None


def resolve_profile(selected: str | None) -> str:
    if selected:
        return selected
    persisted = profile_from_template_file()
    if persisted:
        return persisted
    return "local"


def sync_command(
    profile: str, *, use_dev_dependencies: bool, python_path: str | None = None
) -> list[str]:
    command = uv_command_prefix(python_path) + ["sync"]
    if profile == "cloud":
        command.extend(["--extra", "local", "--extra", "cloud"])
    if use_dev_dependencies:
        command.extend(["--group", "dev-local"])
        if profile == "cloud":
            command.extend(["--group", "dev-cloud"])
    else:
        command.append("--no-dev")
    return command


def lock_command(python_path: str | None = None) -> list[str]:
    return uv_command_prefix(python_path) + ["lock", "--upgrade"]


def uv_environment() -> dict[str, str]:
    env = os.environ.copy()
    if "UV_LINK_MODE" not in env and "OneDrive" in str(REPO_ROOT):
        env["UV_LINK_MODE"] = "copy"
    return env


def remove_readonly(func, path, exc_info) -> None:  # pragma: no cover - platform callback
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def reset_venv() -> None:
    resolved = VENV_DIR.resolve()
    if resolved == REPO_ROOT.resolve() or resolved.parent != REPO_ROOT.resolve():
        raise RuntimeError(f"Refusing to remove unexpected environment path: {resolved}")
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, onexc=remove_readonly)


def is_permission_sync_error(error: subprocess.CalledProcessError) -> bool:
    text = ""
    if error.stdout:
        text += error.stdout
    if error.stderr:
        text += error.stderr
    lowered = text.lower()
    return "failed to remove directory" in lowered or "access denied" in lowered or "acceso denegado" in lowered


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
    *, dry_run: bool, profile: str, use_dev_dependencies: bool, python_path: str | None
) -> None:
    command = sync_command(
        profile, use_dev_dependencies=use_dev_dependencies, python_path=python_path
    )
    try:
        run(command, dry_run=dry_run)
    except subprocess.CalledProcessError as error:
        if dry_run or not is_permission_sync_error(error):
            raise
        print("uv sync hit a locked or inconsistent .venv. Rebuilding the environment and retrying...")
        try:
            reset_venv()
        except OSError as reset_error:
            raise SystemExit(
                "Could not reset .venv because some files are still in use. Close editors, terminals, or background tools using the environment and run `make uv-reset`."
            ) from reset_error
        run(command, dry_run=False)


def run_update(
    *, dry_run: bool, profile: str, use_dev_dependencies: bool, python_path: str | None
) -> None:
    try:
        run(lock_command(python_path), dry_run=dry_run)
        run(
            sync_command(
                profile,
                use_dev_dependencies=use_dev_dependencies,
                python_path=python_path,
            ),
            dry_run=dry_run,
        )
    except subprocess.CalledProcessError as error:
        if not dry_run and is_permission_sync_error(error):
            raise SystemExit(
                "uv update could not clean the current .venv. Close tools using the environment and run `make uv-reset`."
            ) from error
        raise


def run_reset(
    *, dry_run: bool, profile: str, use_dev_dependencies: bool, python_path: str | None
) -> None:
    print(f"Resetting {VENV_DIR}")
    if not dry_run:
        try:
            reset_venv()
        except OSError as error:
            raise SystemExit(
                "Could not remove .venv because some files are still in use. Close editors, terminals, or background tools using the environment and retry `make uv-reset`."
            ) from error
    run(
        sync_command(
            profile, use_dev_dependencies=use_dev_dependencies, python_path=python_path
        ),
        dry_run=dry_run,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run uv environment sync commands with profile-aware recovery behavior."
    )
    parser.add_argument("mode", choices=("init", "update", "reset"))
    parser.add_argument("--profile", choices=sorted(ENVIRONMENT_PROFILES))
    parser.add_argument(
        "--python-path",
        help="Use this Python interpreter for `python -m uv` when uv is not available in PATH.",
    )
    dev_group = parser.add_mutually_exclusive_group()
    dev_group.add_argument(
        "--include-dev",
        action="store_true",
        help="Install dev dependency groups for the selected profile.",
    )
    dev_group.add_argument(
        "--no-dev",
        action="store_true",
        help="Skip dev dependency groups and sync only runtime dependencies.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the uv commands without executing them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.python_path and not Path(args.python_path).exists():
        raise SystemExit(f"Python not found at '{args.python_path}'.")

    profile = resolve_profile(args.profile)
    use_dev_dependencies = not args.no_dev
    if args.mode == "init":
        run_init(
            dry_run=args.dry_run,
            profile=profile,
            use_dev_dependencies=use_dev_dependencies,
            python_path=args.python_path,
        )
        return
    if args.mode == "update":
        run_update(
            dry_run=args.dry_run,
            profile=profile,
            use_dev_dependencies=use_dev_dependencies,
            python_path=args.python_path,
        )
        return
    run_reset(
        dry_run=args.dry_run,
        profile=profile,
        use_dev_dependencies=use_dev_dependencies,
        python_path=args.python_path,
    )


if __name__ == "__main__":
    main()
