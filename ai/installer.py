from __future__ import annotations

import re
import shutil
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
TARGET_GITIGNORE_ENTRIES = (".ai/", "AGENTS.md", "Makefile")
OPTIONAL_TOP_LEVEL_DIRS = {"infra", "src", "tests"}
ENVIRONMENT_PROFILES = {"local", "cloud"}
REQUIREMENTS_PATH = Path("requirements.txt")
LOCAL_REQUIREMENTS_PATH = Path("requirements.local.txt")
CLOUD_REQUIREMENTS_PATH = Path("requirements.cloud.txt")
DEV_REQUIREMENTS_PATH = Path("requirements.dev.txt")

EXCLUDED_DIRS = {
    ".ai",
    ".git",
    ".venv",
    ".vscode",
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
            input(
                "Copy optional project structure folders (src/, infra/, and tests/)? [y/N]: "
            )
            .strip()
            .lower()
        )
        if selected in {"", "n", "no"}:
            return False
        if selected in {"y", "yes"}:
            return True
        print("Please answer yes or no.")


def prompt_environment_profile() -> str:
    while True:
        selected = input("Is the host project local or cloud? [local/cloud]: ").strip()
        normalized = selected.lower()
        if normalized in ENVIRONMENT_PROFILES:
            return normalized
        print("Please answer local or cloud.")


def validate_target(target: Path) -> Path:
    target = target.expanduser().resolve()
    template = TEMPLATE_ROOT.resolve()

    if target == template:
        raise ValueError("Target cannot be the template repository itself.")
    if template in target.parents:
        raise ValueError("Target cannot be inside the template repository.")

    return target


def validate_environment_profile(environment_profile: str) -> str:
    normalized = environment_profile.strip().lower()
    if normalized not in ENVIRONMENT_PROFILES:
        raise ValueError("Environment profile must be 'local' or 'cloud'.")
    return normalized


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


def normalize_requirement_name(line: str) -> str | None:
    requirement = line.split("#", 1)[0].strip()
    if not requirement or requirement.startswith(("-", "--")):
        return None
    match = re.match(r"([A-Za-z0-9_.-]+)", requirement)
    if not match:
        return None
    return match.group(1).lower().replace("_", "-")


def requirements_paths_for_profile(environment_profile: str) -> list[Path]:
    if environment_profile == "local":
        return [LOCAL_REQUIREMENTS_PATH, DEV_REQUIREMENTS_PATH]
    return [CLOUD_REQUIREMENTS_PATH, DEV_REQUIREMENTS_PATH]


def filtered_template_requirements(environment_profile: str) -> list[str]:
    filtered: list[str] = []
    for requirements_path in requirements_paths_for_profile(environment_profile):
        lines = (TEMPLATE_ROOT / requirements_path).read_text(encoding="utf-8").splitlines()
        if filtered and filtered[-1].strip():
            filtered.append("")
        filtered.extend(lines)

    while filtered and not filtered[0].strip():
        filtered.pop(0)
    while filtered and not filtered[-1].strip():
        filtered.pop()

    return filtered


def merge_requirements_content(
    existing_lines: list[str], template_lines: list[str]
) -> list[str]:
    existing_packages = {
        package_name
        for line in existing_lines
        if (package_name := normalize_requirement_name(line))
    }
    pending_lines: list[str] = []

    for line in template_lines:
        package_name = normalize_requirement_name(line)
        if package_name:
            if package_name in existing_packages:
                continue
            existing_packages.add(package_name)
            pending_lines.append(line)
            continue
        pending_lines.append(line)

    while pending_lines and not pending_lines[0].strip():
        pending_lines.pop(0)
    while pending_lines and not pending_lines[-1].strip():
        pending_lines.pop()

    merged = list(existing_lines)
    if not pending_lines:
        return merged

    if merged and merged[-1].strip():
        merged.append("")
    merged.append("# Template dependencies")
    merged.extend(pending_lines)
    return merged


def render_requirements_file(lines: list[str]) -> str:
    return "\n".join(lines).rstrip() + "\n"


def write_requirements_file(
    target: Path,
    dry_run: bool,
    environment_profile: str,
) -> tuple[bool, bool]:
    destination = target / REQUIREMENTS_PATH
    template_lines = filtered_template_requirements(environment_profile)
    target_exists = destination.exists()

    if target_exists:
        existing_lines = destination.read_text(encoding="utf-8").splitlines()
        rendered = render_requirements_file(
            merge_requirements_content(existing_lines, template_lines)
        )
    else:
        rendered = render_requirements_file(template_lines)

    current = destination.read_text(encoding="utf-8") if target_exists else None
    changed = current != rendered

    if changed and not dry_run:
        destination.write_text(rendered, encoding="utf-8")

    return changed, target_exists


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
    target: Path,
    force: bool,
    dry_run: bool,
    *,
    include_structure: bool,
    environment_profile: str,
) -> dict[str, list[str]]:
    target = validate_target(target)
    environment_profile = validate_environment_profile(environment_profile)
    candidates, ignored_paths = iter_template_files(include_structure=include_structure)
    copied: list[str] = []
    skipped: list[str] = []
    created_dirs: set[str] = set()
    updated: list[str] = []

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for source_path in candidates:
        relative = source_path.relative_to(TEMPLATE_ROOT)
        destination = target / relative
        relative_text = relative.as_posix()

        if relative == REQUIREMENTS_PATH:
            continue

        if destination.exists() and not force:
            skipped.append(relative_text)
            continue

        copied.append(relative_text)
        _ensure_destination_parent(target, destination, created_dirs, dry_run)
        if dry_run:
            continue

        shutil.copy2(source_path, destination)

    requirements_changed, requirements_exists = write_requirements_file(
        target=target,
        dry_run=dry_run,
        environment_profile=environment_profile,
    )
    if requirements_changed:
        if requirements_exists:
            updated.append(REQUIREMENTS_PATH.as_posix())
        else:
            copied.append(REQUIREMENTS_PATH.as_posix())
            _ensure_destination_parent(
                target,
                target / REQUIREMENTS_PATH,
                created_dirs,
                dry_run,
            )

    gitignore_updates = append_target_gitignore(target, dry_run=dry_run)

    return {
        "copied": copied,
        "updated": updated,
        "skipped": skipped,
        "ignored": [relative_path(path) for path in ignored_paths],
        "created_dirs": sorted(created_dirs),
        "gitignore_updates": gitignore_updates,
    }


def print_summary(summary: dict[str, list[str]], dry_run: bool) -> None:
    mode = "Dry run" if dry_run else "Install"
    print(f"{mode} summary")
    print(f"- Copied: {len(summary['copied'])}")
    print(f"- Updated: {len(summary['updated'])}")
    print(f"- Skipped existing: {len(summary['skipped'])}")
    print(f"- Ignored: {len(summary['ignored'])}")
    print(f"- Directories created: {len(summary['created_dirs'])}")
    print(f"- .gitignore entries added: {len(summary['gitignore_updates'])}")

    for key in (
        "copied",
        "updated",
        "skipped",
        "ignored",
        "created_dirs",
        "gitignore_updates",
    ):
        values = summary[key]
        if not values:
            continue
        print(f"\n{key.replace('_', ' ').title()}:")
        for value in values:
            print(f"  {value}")
