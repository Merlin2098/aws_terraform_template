from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from tkinter import Tk, filedialog


TEMPLATE_ROOT = Path(__file__).resolve().parent
TARGET_GITIGNORE_ENTRIES = ("ai/", "AGENTS.md", "Makefile")
REQUIRED_TARGET_DIRS = ("infra/env", "infra/modules")

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "docs",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "logs",
}
EXCLUDED_EXACT_FILES = {
    "main.py",
    "infra/crash.log",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".zip",
}


def select_target_folder() -> Path:
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(
        title="Select the host repository folder",
        mustexist=False,
    )
    root.destroy()

    if not selected:
        raise ValueError("No target folder selected.")

    return Path(selected)


def relative_path(path: Path) -> str:
    return path.relative_to(TEMPLATE_ROOT).as_posix()


def is_excluded(path: Path) -> bool:
    relative = relative_path(path)
    parts = path.relative_to(TEMPLATE_ROOT).parts

    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    if relative in EXCLUDED_EXACT_FILES:
        return True
    if path.name in {"README.md", "Thumbs.db", ".DS_Store"}:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    if relative.startswith("infra/.terraform/"):
        return True
    if relative.startswith("infra/") and (
        path.name.endswith(".tfstate") or ".tfstate." in path.name
    ):
        return True

    return False


def validate_target(target: Path) -> Path:
    target = target.expanduser().resolve()
    template = TEMPLATE_ROOT.resolve()

    if target == template:
        raise ValueError("Target cannot be the template repository itself.")
    if template in target.parents:
        raise ValueError("Target cannot be inside the template repository.")

    return target


def iter_template_files() -> tuple[list[Path], list[Path]]:
    copied_candidates: list[Path] = []
    ignored: list[Path] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if is_excluded(path):
                ignored.append(path)
                continue
            if path.is_dir():
                walk(path)
                continue
            if path.is_file():
                copied_candidates.append(path)

    walk(TEMPLATE_ROOT)

    return copied_candidates, ignored


def existing_gitignore_entries(gitignore_path: Path) -> set[str]:
    if not gitignore_path.exists():
        return set()
    return {
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def append_target_gitignore(target: Path, dry_run: bool) -> list[str]:
    gitignore_path = target / ".gitignore"
    existing = existing_gitignore_entries(gitignore_path)
    missing = [entry for entry in TARGET_GITIGNORE_ENTRIES if entry not in existing]

    if not missing or dry_run:
        return missing

    if gitignore_path.exists():
        current = gitignore_path.read_text(encoding="utf-8")
        needs_leading_newline = bool(current) and not current.endswith("\n")
        prefix = "\n" if needs_leading_newline else ""
        block_prefix = "\n" if current.strip() else ""
        addition = (
            f"{prefix}{block_prefix}"
            "# Local template helper files\n"
            + "\n".join(missing)
            + "\n"
        )
        gitignore_path.write_text(current + addition, encoding="utf-8")
    else:
        gitignore_path.write_text(
            "# Local template helper files\n" + "\n".join(missing) + "\n",
            encoding="utf-8",
        )

    return missing


def install_template(target: Path, force: bool, dry_run: bool) -> dict[str, list[str]]:
    target = validate_target(target)
    candidates, ignored_paths = iter_template_files()
    copied: list[str] = []
    skipped: list[str] = []
    created_dirs: list[str] = []

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for relative_dir in REQUIRED_TARGET_DIRS:
        destination_dir = target / relative_dir
        if destination_dir.exists():
            continue
        created_dirs.append(relative_dir)
        if not dry_run:
            destination_dir.mkdir(parents=True, exist_ok=True)

    for source_path in candidates:
        relative = source_path.relative_to(TEMPLATE_ROOT)
        destination = target / relative
        relative_text = relative.as_posix()

        if destination.exists() and not force:
            skipped.append(relative_text)
            continue

        copied.append(relative_text)
        if dry_run:
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)

    gitignore_updates = append_target_gitignore(target, dry_run=dry_run)

    return {
        "copied": copied,
        "skipped": skipped,
        "ignored": [relative_path(path) for path in ignored_paths],
        "created_dirs": created_dirs,
        "gitignore_updates": gitignore_updates,
    }


def print_summary(summary: dict[str, list[str]], dry_run: bool) -> None:
    mode = "Dry run" if dry_run else "Install"
    print(f"{mode} summary")
    print(f"- Copied: {len(summary['copied'])}")
    print(f"- Skipped existing: {len(summary['skipped'])}")
    print(f"- Ignored: {len(summary['ignored'])}")
    print(f"- Directories created: {len(summary['created_dirs'])}")
    print(f"- .gitignore entries added: {len(summary['gitignore_updates'])}")

    for key in ("copied", "skipped", "ignored", "created_dirs", "gitignore_updates"):
        values = summary[key]
        if not values:
            continue
        print(f"\n{key.replace('_', ' ').title()}:")
        for value in values:
            print(f"  {value}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install this AWS Terraform template into another repository."
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Destination repository directory. If omitted, a folder picker opens.",
    )
    parser.add_argument(
        "--select-target",
        action="store_true",
        help="Open a folder picker to select the destination repository directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing target files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the files that would be copied without writing anything.",
    )
    args = parser.parse_args()

    try:
        target = select_target_folder() if args.select_target or not args.target else args.target
        summary = install_template(
            target=target,
            force=args.force,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        parser.error(str(exc))

    print_summary(summary, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
