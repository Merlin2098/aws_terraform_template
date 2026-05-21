from __future__ import annotations

import shutil
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_GITIGNORE_PATH = TEMPLATE_ROOT / ".gitignore"
TEMPLATE_PROFILE_PATH = Path(".template-profile")
OPTIONAL_TOP_LEVEL_DIRS = {"infra", "src", "tests"}
OPTIONAL_EMPTY_DIRS = {"tests"}
CLOUD_ONLY_TOP_LEVEL_DIRS = {"specs"}
ENVIRONMENT_PROFILES = {"local", "cloud"}
PACKAGE_MANAGERS = {"pip", "uv"}
LOCAL_REQUIREMENTS_PATH = Path("requirements.local.txt")
CLOUD_REQUIREMENTS_PATH = Path("requirements.cloud.txt")
DEV_REQUIREMENTS_PATH = Path("requirements.dev.txt")
PYPROJECT_PATH = Path("pyproject.toml")
UV_LOCK_PATH = Path("uv.lock")

EXCLUDED_DIRS = {
    ".ai",
    ".git",
    ".venv",
    ".vscode",
    "build",
    "dist",
    "logs",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".pytest-tmp",
    ".ruff_cache",
}
EXCLUDED_EXACT_FILES = {
    "ai/installer.py",
    "infra/crash.log",
    "install_linux.py",
    "install_windows.py",
    ".claude/settings.local.json",
}
# Entries added to the host .gitignore that are not in the template's own
# .gitignore — they apply to host repos but not to the template itself.
HOST_EXTRA_GITIGNORE_ENTRIES = [
    "ai/",                        # host: AI guidance is inherited read-only from the template
    "specs/template/",            # host: template specs are inherited read-only from the template
    "specs/README.md",            # host: template-owned specs index
    "docs/linux_setup/",          # host: template-owned Linux setup guide
    "docs/windows_setup/",        # host: template-owned Windows setup guide
    "docs/terra_principles.md",   # host: template-owned Terraform principles doc
    "docs/terraform_cheatsheet.md", # host: template-owned Terraform cheat sheet
    "docs/treemap.md",            # host: template-owned repo treemap
    "data/",                      # host: runtime data
    "/prompt/",                   # host: workflow scratch
    ".claude/settings.local.json", # host: personal Claude Code settings
]
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
    if path.name.startswith("pytest-cache-files-"):
        return True
    if relative in EXCLUDED_EXACT_FILES:
        return True
    if path.name in {"README.md", "Thumbs.db", ".DS_Store"} and not relative.startswith(
        "specs/"
    ):
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


def prompt_package_manager() -> str:
    while True:
        selected = input("Use pip or uv for host dependencies? [pip/uv]: ").strip()
        normalized = selected.lower()
        if normalized in PACKAGE_MANAGERS:
            return normalized
        print("Please answer pip or uv.")


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


def validate_package_manager(package_manager: str) -> str:
    normalized = package_manager.strip().lower()
    if normalized not in PACKAGE_MANAGERS:
        raise ValueError("Package manager must be 'pip' or 'uv'.")
    return normalized


def should_copy_requirements_file(relative: Path, environment_profile: str) -> bool:
    if relative == LOCAL_REQUIREMENTS_PATH:
        return environment_profile in {"local", "cloud"}
    if relative == CLOUD_REQUIREMENTS_PATH:
        return environment_profile == "cloud"
    if relative == DEV_REQUIREMENTS_PATH:
        return True
    return True


def should_copy_package_file(
    relative: Path, environment_profile: str, package_manager: str
) -> bool:
    if relative == TEMPLATE_PROFILE_PATH:
        return package_manager == "uv"
    if relative.name.startswith("requirements"):
        return package_manager == "pip" and should_copy_requirements_file(
            relative, environment_profile
        )
    if relative in {PYPROJECT_PATH, UV_LOCK_PATH}:
        return package_manager == "uv"
    return True


def should_copy_structure_path(relative: Path, include_structure: bool) -> bool:
    if not relative.parts:
        return True
    top_level = relative.parts[0]
    if not include_structure and top_level in OPTIONAL_TOP_LEVEL_DIRS:
        return False
    if (
        include_structure
        and top_level in OPTIONAL_EMPTY_DIRS
        and len(relative.parts) > 1
    ):
        return False
    return True


def should_copy_specs_path(relative: Path, environment_profile: str) -> bool:
    if not relative.parts:
        return True
    if (
        relative.parts[0] in CLOUD_ONLY_TOP_LEVEL_DIRS
        and environment_profile != "cloud"
    ):
        return False
    return True


def iter_template_files(
    *, include_structure: bool, environment_profile: str, package_manager: str
) -> tuple[list[Path], list[Path]]:
    copied_candidates: list[Path] = []
    ignored: list[Path] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            relative = path.relative_to(TEMPLATE_ROOT)
            if not should_copy_structure_path(relative, include_structure):
                ignored.append(path)
                continue
            if not should_copy_specs_path(relative, environment_profile):
                ignored.append(path)
                continue
            if not should_copy_package_file(
                relative, environment_profile, package_manager
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


def render_target_file(
    source_text: str,
    *,
    relative: Path,
    package_manager: str,
    environment_profile: str,
) -> str:
    if relative == Path(".pre-commit-config.yaml"):
        if package_manager == "uv":
            return source_text
        return source_text.replace(
            "args: [--manager, uv]",
            f"args: [--manager, {package_manager}, --profile, {environment_profile}]",
        )
    if relative == Path("Makefile"):
        if package_manager == "uv":
            init_command = "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init"
            package_command = "uv run python scripts/package.py --package-manager uv"
        else:
            init_command = (
                f"$(BOOTSTRAP_PYTHON) scripts/run_pip_init.py --profile {environment_profile}"
            )
            package_command = "$(PYTHON) scripts/package.py"
        return (
            source_text.replace(
                "$(BOOTSTRAP_PYTHON) scripts/run_pip_init.py",
                init_command,
            )
            .replace("$(PYTHON) scripts/package.py", package_command)
        )
    if relative == TEMPLATE_PROFILE_PATH:
        return (
            f"package_manager={package_manager}\n"
            f"environment_profile={environment_profile}\n"
        )
    return source_text


def copy_template_file(
    source_path: Path,
    destination: Path,
    *,
    relative: Path,
    package_manager: str,
    environment_profile: str,
) -> None:
    if relative in {Path(".pre-commit-config.yaml"), Path("Makefile"), TEMPLATE_PROFILE_PATH}:
        source_text = source_path.read_text(encoding="utf-8")
        destination.write_text(
            render_target_file(
                source_text,
                relative=relative,
                package_manager=package_manager,
                environment_profile=environment_profile,
            ),
            encoding="utf-8",
        )
        shutil.copystat(source_path, destination)
        return
    shutil.copy2(source_path, destination)


def existing_gitignore_entries(gitignore_path: Path) -> set[str]:
    if not gitignore_path.exists():
        return set()
    return {
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def template_gitignore_entries() -> list[str]:
    from_template = [
        line.strip()
        for line in TEMPLATE_GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    seen = set(from_template)
    extras = [e for e in HOST_EXTRA_GITIGNORE_ENTRIES if e not in seen]
    return from_template + extras


def append_target_gitignore(target: Path, dry_run: bool) -> list[str]:
    gitignore_path = target / ".gitignore"
    if not gitignore_path.exists():
        return []

    existing = existing_gitignore_entries(gitignore_path)
    missing = [
        entry for entry in template_gitignore_entries() if entry not in existing
    ]

    if not missing or dry_run:
        return missing

    current = gitignore_path.read_text(encoding="utf-8")
    needs_leading_newline = bool(current) and not current.endswith("\n")
    prefix = "\n" if needs_leading_newline else ""
    block_prefix = "\n" if current.strip() else ""
    addition = (
        f"{prefix}{block_prefix}"
        "# Missing entries from template .gitignore\n" + "\n".join(missing) + "\n"
    )
    gitignore_path.write_text(current + addition, encoding="utf-8")

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


def create_optional_empty_dirs(
    target: Path, *, include_structure: bool, dry_run: bool
) -> list[str]:
    if not include_structure:
        return []

    created: list[str] = []
    for dirname in sorted(OPTIONAL_EMPTY_DIRS):
        destination = target / dirname
        created.append(dirname)
        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)
    return created


def install_template(
    target: Path,
    force: bool,
    dry_run: bool,
    *,
    include_structure: bool,
    environment_profile: str,
    package_manager: str = "pip",
) -> dict[str, list[str]]:
    target = validate_target(target)
    environment_profile = validate_environment_profile(environment_profile)
    package_manager = validate_package_manager(package_manager)
    candidates, ignored_paths = iter_template_files(
        include_structure=include_structure,
        environment_profile=environment_profile,
        package_manager=package_manager,
    )
    copied: list[str] = []
    skipped: list[str] = []
    created_dirs: set[str] = set()

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for dirname in create_optional_empty_dirs(
        target, include_structure=include_structure, dry_run=dry_run
    ):
        created_dirs.add(dirname)

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

        copy_template_file(
            source_path,
            destination,
            relative=relative,
            package_manager=package_manager,
            environment_profile=environment_profile,
        )
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

    for key in (
        "copied",
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
