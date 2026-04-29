from __future__ import annotations

import shutil
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
TARGET_GITIGNORE_ENTRIES = ("ai/", "AGENTS.md", "Makefile")
OPTIONAL_TOP_LEVEL_DIRS = {"infra", "src"}

EXCLUDED_DIRS = {
    ".ai",
    ".git",
    ".venv",
    "build",
    "dist",
    "docs",
    "logs",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
EXCLUDED_EXACT_FILES = {
    "ai/installer.py",
    "infra/crash.log",
    "install_linux.py",
    "install_windows.py",
}
EXCLUDED_SUFFIXES = {
    ".log",
    ".pyc",
    ".pyd",
    ".pyo",
    ".zip",
}


def select_target_folder() -> Path:
    from tkinter import Tk, filedialog

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


def prompt_include_structure() -> bool:
    while True:
        selected = (
            input("Copy optional project structure folders (src/ and infra/)? [y/N]: ")
            .strip()
            .lower()
        )
        if selected in {"", "n", "no"}:
            return False
        if selected in {"y", "yes"}:
            return True
        print("Please answer yes or no.")


def validate_target(target: Path) -> Path:
    target = target.expanduser().resolve()
    template = TEMPLATE_ROOT.resolve()

    if target == template:
        raise ValueError("Target cannot be the template repository itself.")
    if template in target.parents:
        raise ValueError("Target cannot be inside the template repository.")

    return target


def iter_template_files(*, include_structure: bool) -> tuple[list[Path], list[Path]]:
    copied_candidates: list[Path] = []
    ignored: list[Path] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            relative = path.relative_to(TEMPLATE_ROOT)
            if (
                not include_structure
                and relative.parts
                and relative.parts[0] in OPTIONAL_TOP_LEVEL_DIRS
            ):
                ignored.append(path)
                continue
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
            "# Local template helper files\n" + "\n".join(missing) + "\n"
        )
        gitignore_path.write_text(current + addition, encoding="utf-8")
    else:
        gitignore_path.write_text(
            "# Local template helper files\n" + "\n".join(missing) + "\n",
            encoding="utf-8",
        )

    return missing


def _ensure_destination_parent(
    target: Path,
    destination: Path,
    created_dirs: set[str],
    dry_run: bool,
) -> None:
    pending: list[Path] = []
    current = destination.parent

    while current != target and not current.exists():
        pending.append(current)
        current = current.parent

    for directory in reversed(pending):
        created_dirs.add(directory.relative_to(target).as_posix())
        if not dry_run:
            directory.mkdir(parents=True, exist_ok=True)


def install_template(
    target: Path, force: bool, dry_run: bool, *, include_structure: bool
) -> dict[str, list[str]]:
    target = validate_target(target)
    candidates, ignored_paths = iter_template_files(include_structure=include_structure)
    copied: list[str] = []
    skipped: list[str] = []
    created_dirs: set[str] = set()

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for source_path in candidates:
        relative = source_path.relative_to(TEMPLATE_ROOT)
        destination = target / relative
        relative_text = relative.as_posix()

        if destination.exists() and not force:
            skipped.append(relative_text)
            continue

        copied.append(relative_text)
        _ensure_destination_parent(target, destination, created_dirs, dry_run)
        if dry_run:
            continue

        shutil.copy2(source_path, destination)

    gitignore_updates = append_target_gitignore(target, dry_run=dry_run)

    return {
        "copied": copied,
        "skipped": skipped,
        "ignored": [relative_path(path) for path in ignored_paths],
        "created_dirs": sorted(created_dirs),
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
