from __future__ import annotations

# Divergence detection via content fingerprints — ADR-FW-003.
# framework_manifest is a {path: {sha256, ownership}} map; tree_digest is the
# aggregate hash of the framework-owned tree.  framework_version is retained as
# a governance label (changelog/breaking-change anchor), not as a sync detector.

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ai.runtime.capability_registry import (
    CapabilityDescriptor,
    load_registry,
)
from ai.runtime.profile import PROFILE_FILENAME, profile_document, render_profile
from ai.runtime.project_profile import parse_capability_id


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_GITIGNORE_PATH = TEMPLATE_ROOT / ".gitignore"
TEMPLATE_PROFILE_PATH = Path(PROFILE_FILENAME)
OPTIONAL_TOP_LEVEL_DIRS = {"infra", "src", "tests"}
OPTIONAL_EMPTY_DIRS = {"tests"}
PYPROJECT_PATH = Path("pyproject.toml")
UV_LOCK_PATH = Path("uv.lock")
STATE_FILENAME = ".framework-version.json"
HOST_OWNED_TOP_LEVEL = {"src", "infra", "tests"}
HOST_OWNED_PATHS = {"specs/project"}

EXCLUDED_DIRS = {
    ".ai",
    ".git",
    ".venv",
    ".vscode",
    "build",
    "dist",
    "docs",
    "logs",
    "reusable",  # host-owned: project-specific templates, not framework artefacts
    "specs",
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
    # Host-owned root files: never distributed or overwritten by the framework.
    # Makefile and .claude/settings.json may be customised per host.
    "Makefile",
    "uv.lock",
    ".claude/settings.json",
}

# Files that are copied once on first install (if absent) but are never
# overwritten on update — only missing *entries* are merged in.
# pyproject.toml: host manages its own dependencies, name, version.
# .pre-commit-config.yaml: host may add its own hooks.
APPEND_ONLY_FILES = {
    "pyproject.toml",
    ".pre-commit-config.yaml",
}
# Entries added to the host .gitignore that are not in the template's own
# .gitignore — they apply to host repos but not to the template itself.
HOST_EXTRA_GITIGNORE_ENTRIES = [
    "ai/",  # host: AI guidance is inherited read-only from the template
    "data/",  # host: runtime data
    "/prompt/",  # host: workflow scratch
    ".claude/settings.local.json",  # host: personal Claude Code settings
]
EXCLUDED_SUFFIXES = {
    ".log",
    ".pyc",
    ".pyd",
    ".pyo",
    ".zip",
}

# ADR-FW-003: ownership values.
# `generated`    = rendered at install time (not a byte-for-byte copy of template).
# `managed`      = framework owns; host should not edit; overwritten on update.
# `append-only`  = copied once on first install; on update only missing entries
#                  are merged in (e.g. pyproject.toml, .pre-commit-config.yaml).
# `template`     is reserved for a future explicit set — Phase 1 maps remaining
#                non-generated, non-append-only files to `managed`.
OWNERSHIP_GENERATED = "generated"
OWNERSHIP_MANAGED = "managed"
OWNERSHIP_APPEND_ONLY = "append-only"


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------


def _normalize_for_hash(data: bytes) -> bytes:
    """Normalize line endings (CRLF/CR → LF) before hashing."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def file_sha256(path: Path) -> str:
    """SHA-256 of a file on disk, with EOL normalization."""
    raw = path.read_bytes()
    return hashlib.sha256(_normalize_for_hash(raw)).hexdigest()


def text_sha256(text: str) -> str:
    """SHA-256 of an in-memory text string, with EOL normalization."""
    raw = text.encode("utf-8")
    return hashlib.sha256(_normalize_for_hash(raw)).hexdigest()


def classify_ownership(relative: Path) -> str:
    """Return the ownership class for a framework-distributed path."""
    if relative == TEMPLATE_PROFILE_PATH:
        return OWNERSHIP_GENERATED
    if relative.as_posix() in APPEND_ONLY_FILES:
        return OWNERSHIP_APPEND_ONLY
    return OWNERSHIP_MANAGED


def compute_tree_digest(manifest: dict[str, dict]) -> str:
    """Aggregate hash over sorted (path, sha256) pairs in the manifest.

    Stable ordering + EOL-normalised sha256 values make this deterministic
    across platforms.
    """
    h = hashlib.sha256()
    for path in sorted(manifest):
        entry = manifest[path]
        sha = entry.get("sha256") or ""
        h.update(f"{path}:{sha}\n".encode())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# State I/O helpers
# ---------------------------------------------------------------------------


def _manifest_as_map(
    raw_manifest: list | dict | None,
) -> dict[str, dict]:
    """Normalise legacy list manifests to the new map format.

    Legacy format (list[str]):   ["AGENTS.md", "ai/skills/..."]
    New format   (dict):         {"AGENTS.md": {"sha256": "...", "ownership": "managed"}}

    Unknown sha256 values from legacy state are stored as None so callers can
    detect the missing-hash case and treat it as a forced update.
    """
    if raw_manifest is None:
        return {}
    if isinstance(raw_manifest, dict):
        return raw_manifest
    # Legacy list — convert; ownership is derived from path.
    result: dict[str, dict] = {}
    for entry in raw_manifest:
        rel = Path(entry)
        result[entry] = {
            "sha256": None,
            "ownership": classify_ownership(rel),
        }
    return result


def framework_version() -> str:
    pyproject = TEMPLATE_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not find version in {pyproject}")
    return match.group(1)


def is_framework_owned(relative: Path) -> bool:
    parts = relative.parts
    if not parts:
        return False
    top = parts[0]
    if top in HOST_OWNED_TOP_LEVEL:
        return False
    rel_str = relative.as_posix()
    for host_path in HOST_OWNED_PATHS:
        if rel_str == host_path or rel_str.startswith(host_path + "/"):
            return False
    if relative == TEMPLATE_PROFILE_PATH:
        return False
    return True


def read_state(target: Path) -> dict | None:
    state_path = target / STATE_FILENAME
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_state(
    target: Path,
    *,
    version: str,
    include_structure: bool,
    enabled_capabilities: list[str],
    manifest: dict[str, dict],
    tree_digest: str,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    state = {
        "framework_version": version,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "include_structure": include_structure,
        "enabled_capabilities": enabled_capabilities,
        "tree_digest": tree_digest,
        "framework_manifest": {k: manifest[k] for k in sorted(manifest)},
    }
    state_path = target / STATE_FILENAME
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Path / file predicates
# ---------------------------------------------------------------------------


def is_excluded(path: Path) -> bool:
    relative = relative_path(path)
    parts = path.relative_to(TEMPLATE_ROOT).parts

    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    if path.name.startswith("pytest-cache-files-"):
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


def available_capability_ids(
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> list[str]:
    registry = registry or load_registry(TEMPLATE_ROOT)
    return [
        f"{category}:{name}"
        for category in sorted(registry)
        for name in sorted(registry[category])
    ]


def prompt_enabled_capabilities(
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> list[str]:
    registry = registry or load_registry(TEMPLATE_ROOT)
    identifiers = available_capability_ids(registry)
    print("Available capabilities:")
    for index, identifier in enumerate(identifiers, start=1):
        print(f"  {index}. {identifier}")
    selected = input(
        "Capabilities to enable (comma-separated numbers, empty for all, "
        "'none' for none): "
    ).strip()
    if not selected:
        return available_capability_ids(registry)
    if selected.strip().lower() == "none":
        return validate_enabled_capabilities(["none"], registry)

    values: list[str] = []
    for token in selected.split(","):
        token = token.strip()
        if not token:
            continue
        if not token.isdigit():
            raise ValueError(f"Invalid capability number '{token}'.")
        position = int(token)
        if not 1 <= position <= len(identifiers):
            raise ValueError(
                f"Capability number {position} is out of range "
                f"(1-{len(identifiers)})."
            )
        values.append(identifiers[position - 1])

    return validate_enabled_capabilities(values, registry)


def validate_target(target: Path) -> Path:
    target = target.expanduser().resolve()
    template = TEMPLATE_ROOT.resolve()

    if target == template:
        raise ValueError("Target cannot be the template repository itself.")
    if template in target.parents:
        raise ValueError("Target cannot be inside the template repository.")

    return target


def validate_enabled_capabilities(
    values: list[str],
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> list[str]:
    registry = registry or load_registry(TEMPLATE_ROOT)
    if not values:
        return available_capability_ids(registry)
    lowered = [value.strip().lower() for value in values]
    if "none" in lowered:
        if len(lowered) != 1:
            raise ValueError("'none' cannot be combined with other capabilities.")
        return []

    normalized: list[str] = []
    for value in lowered:
        category, name = parse_capability_id(value)
        if category not in registry or name not in registry[category]:
            raise ValueError(
                f"Unknown capability '{category}:{name}'. Available values: "
                f"{', '.join(available_capability_ids(registry))}."
            )
        identifier = f"{category}:{name}"
        if identifier not in normalized:
            normalized.append(identifier)
    return normalized


def capability_selection(values: list[str]) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    for value in values:
        category, name = parse_capability_id(value)
        selected.setdefault(category, []).append(name)
    return selected


def should_copy_package_file(relative: Path) -> bool:
    if relative.name.startswith("requirements"):
        return False
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


def iter_template_files(
    *,
    include_structure: bool,
) -> tuple[list[Path], list[Path]]:
    copied_candidates: list[Path] = []
    ignored: list[Path] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            relative = path.relative_to(TEMPLATE_ROOT)
            if not should_copy_structure_path(relative, include_structure):
                ignored.append(path)
                continue
            if not should_copy_package_file(relative):
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
    capabilities: dict[str, list[str]] | None = None,
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> str:
    if relative == TEMPLATE_PROFILE_PATH:
        registry = registry or load_registry(TEMPLATE_ROOT)
        return render_profile(
            profile_document(
                registry,
                enabled=capabilities or {},
            )
        )
    return source_text


def copy_template_file(
    source_path: Path,
    destination: Path,
    *,
    relative: Path,
    capabilities: dict[str, list[str]] | None = None,
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> None:
    if relative == TEMPLATE_PROFILE_PATH:
        source_text = source_path.read_text(encoding="utf-8")
        destination.write_text(
            render_target_file(
                source_text,
                relative=relative,
                capabilities=capabilities,
                registry=registry,
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
    missing = [entry for entry in template_gitignore_entries() if entry not in existing]

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


# ---------------------------------------------------------------------------
# Append-only merge helpers
# ---------------------------------------------------------------------------


def _merge_pyproject(template_path: Path, host_path: Path, dry_run: bool) -> list[str]:
    """Merge missing top-level TOML sections from template into host pyproject.toml.

    Only adds sections the host is missing entirely (e.g. [tool.ruff],
    [tool.pytest.ini_options]).  Never modifies [project] or existing sections.
    Returns list of added section headers.
    """
    import tomllib

    template_text = template_path.read_text(encoding="utf-8")
    host_text = host_path.read_text(encoding="utf-8")

    try:
        template_doc = tomllib.loads(template_text)
        host_doc = tomllib.loads(host_text)
    except Exception:
        return []  # malformed TOML — skip silently

    # Never touch [project] — that belongs entirely to the host.
    # Only consider [tool.*] sections and [build-system].
    NEVER_TOUCH = {"project", "project.optional-dependencies", "project.scripts"}
    added: list[str] = []

    additions: list[str] = []
    for section, value in template_doc.items():
        if section in NEVER_TOUCH:
            continue
        if section not in host_doc:
            # Append the raw section block from the template text.
            # Extract the block by finding the header in the template source.
            block = _extract_toml_section(template_text, section)
            if block:
                additions.append(block)
                added.append(f"[{section}]")

    if additions and not dry_run:
        current = host_path.read_text(encoding="utf-8")
        sep = "\n" if current.endswith("\n") else "\n\n"
        host_path.write_text(current + sep + "\n".join(additions), encoding="utf-8")

    return added


def _extract_toml_section(toml_text: str, section: str) -> str:
    """Extract a complete top-level TOML section block as a string."""
    import re

    header = f"[{section}]"
    # Find the header line
    lines = toml_text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i
            break
    if start is None:
        return ""

    # Collect lines until the next top-level section header or EOF.
    block_lines = [lines[start]]
    for line in lines[start + 1 :]:
        stripped = line.strip()
        # A new top-level section: [name] but not [[array]] or [section.sub]
        if re.match(r"^\[[A-Za-z]", stripped) and not stripped.startswith("[["):
            break
        block_lines.append(line)
    return "".join(block_lines).rstrip() + "\n"


def _merge_precommit(template_path: Path, host_path: Path, dry_run: bool) -> list[str]:
    """Merge missing hook ids from template .pre-commit-config.yaml into host.

    Only adds hooks whose `id` is not already present in the host config.
    Returns list of added hook ids.
    """
    import yaml

    try:
        template_doc = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
        host_doc = yaml.safe_load(host_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []

    template_repos = template_doc.get("repos", [])
    host_repos = host_doc.get("repos", [])

    # Collect existing hook ids in host.
    existing_ids: set[str] = set()
    for repo in host_repos:
        for hook in repo.get("hooks", []):
            if hook.get("id"):
                existing_ids.add(hook["id"])

    added: list[str] = []
    for repo in template_repos:
        missing_hooks = [
            h for h in repo.get("hooks", [])
            if h.get("id") and h["id"] not in existing_ids
        ]
        if not missing_hooks:
            continue
        added.extend(h["id"] for h in missing_hooks)
        if dry_run:
            continue
        # Find or create the matching repo entry in the host.
        repo_url = repo.get("repo", "local")
        host_repo = next(
            (r for r in host_repos if r.get("repo") == repo_url), None
        )
        if host_repo is None:
            host_repos.append({"repo": repo_url, "hooks": missing_hooks})
        else:
            host_repo.setdefault("hooks", []).extend(missing_hooks)

    if added and not dry_run:
        host_doc["repos"] = host_repos
        host_path.write_text(
            yaml.safe_dump(host_doc, sort_keys=False, default_flow_style=False,
                           allow_unicode=True),
            encoding="utf-8",
        )

    return added


def merge_append_only_file(
    template_path: Path,
    host_path: Path,
    *,
    relative: Path,
    dry_run: bool,
) -> list[str]:
    """Dispatch to the right merge function for an append-only file.

    Returns a list of added items (section names or hook ids).
    """
    rel = relative.as_posix()
    if rel == "pyproject.toml":
        return _merge_pyproject(template_path, host_path, dry_run)
    if rel == ".pre-commit-config.yaml":
        return _merge_precommit(template_path, host_path, dry_run)
    return []


# ---------------------------------------------------------------------------
# Manifest / hash helpers shared by install + update
# ---------------------------------------------------------------------------


def _hash_for_template_file(
    source_path: Path,
    *,
    relative: Path,
    capabilities: dict[str, list[str]] | None = None,
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> str:
    """Return the sha256 that will be written to the host for this template file."""
    if relative == TEMPLATE_PROFILE_PATH:
        source_text = source_path.read_text(encoding="utf-8")
        rendered = render_target_file(
            source_text,
            relative=relative,
            capabilities=capabilities,
            registry=registry,
        )
        return text_sha256(rendered)
    return file_sha256(source_path)


def _build_template_manifest(
    candidates: list[Path],
    *,
    capabilities: dict[str, list[str]] | None = None,
    registry: dict[str, dict[str, CapabilityDescriptor]] | None = None,
) -> dict[str, dict]:
    """Build {rel_posix: {sha256, ownership}} for all framework-owned candidates."""
    manifest: dict[str, dict] = {}
    for source_path in candidates:
        relative = source_path.relative_to(TEMPLATE_ROOT)
        if not is_framework_owned(relative):
            continue
        rel_text = relative.as_posix()
        sha = _hash_for_template_file(
            source_path,
            relative=relative,
            capabilities=capabilities,
            registry=registry,
        )
        manifest[rel_text] = {
            "sha256": sha,
            "ownership": classify_ownership(relative),
        }
    return manifest


def _patch_gitignore_hash(
    manifest: dict[str, dict], target: Path, *, dry_run: bool
) -> None:
    """.gitignore is augmented after copy — record the on-disk hash, not the template hash.

    append_target_gitignore may append host-specific entries, so the file on
    disk differs from the template source.  We patch the manifest entry with the
    actual hash so drift detection treats the augmented file as the baseline.
    """
    gitignore_key = ".gitignore"
    if gitignore_key not in manifest:
        return
    host_gitignore = target / ".gitignore"
    if dry_run or not host_gitignore.exists():
        return
    manifest[gitignore_key]["sha256"] = file_sha256(host_gitignore)


def _patch_host_file_hashes(
    manifest: dict[str, dict], target: Path, rel_posix_set: set[str], *, dry_run: bool
) -> None:
    """Replace template-source hashes with actual on-disk hashes for a set of paths.

    Used for append-only files (pyproject.toml, .pre-commit-config.yaml) whose
    host copy may differ from the template source because the host already had
    the file or it was modified post-copy.
    """
    if dry_run:
        return
    for rel_posix in rel_posix_set:
        if rel_posix not in manifest:
            continue
        host_file = target / rel_posix
        if host_file.exists():
            manifest[rel_posix]["sha256"] = file_sha256(host_file)


# ---------------------------------------------------------------------------
# Public API: install
# ---------------------------------------------------------------------------


def install_template(
    target: Path,
    force: bool,
    dry_run: bool,
    *,
    include_structure: bool,
    enabled_capabilities: list[str] | None = None,
) -> dict[str, list[str]]:
    target = validate_target(target)
    registry = load_registry(TEMPLATE_ROOT)
    selections = list(enabled_capabilities or [])
    selections = validate_enabled_capabilities(selections, registry)
    capabilities = capability_selection(selections)
    candidates, ignored_paths = iter_template_files(
        include_structure=include_structure,
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
            capabilities=capabilities,
            registry=registry,
        )
    gitignore_updates = append_target_gitignore(target, dry_run=dry_run)

    # Build manifest with content fingerprints (ADR-FW-003).
    manifest = _build_template_manifest(
        candidates, capabilities=capabilities, registry=registry
    )
    # Files that diverge from the template source after writing must be hashed
    # from the actual on-disk result, not from the template source.
    _patch_gitignore_hash(manifest, target, dry_run=dry_run)
    _patch_host_file_hashes(manifest, target, APPEND_ONLY_FILES, dry_run=dry_run)
    tree_digest = compute_tree_digest(manifest)
    version = framework_version()
    write_state(
        target,
        version=version,
        include_structure=include_structure,
        enabled_capabilities=selections,
        manifest=manifest,
        tree_digest=tree_digest,
        dry_run=dry_run,
    )

    return {
        "copied": copied,
        "skipped": skipped,
        "ignored": [relative_path(path) for path in ignored_paths],
        "created_dirs": sorted(created_dirs),
        "gitignore_updates": gitignore_updates,
    }


# ---------------------------------------------------------------------------
# Public API: update
# ---------------------------------------------------------------------------


def update_template(
    target: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    enabled_capabilities: list[str] | None = None,
    include_structure: bool | None = None,
) -> dict:
    target = validate_target(target)
    state = read_state(target)
    if state is None:
        raise ValueError(
            f"No framework state found in {target}. "
            "Run the installer first (install_windows.py or install_linux.py)."
        )

    resolved_include_structure = (
        include_structure
        if include_structure is not None
        else state.get("include_structure", False)
    )
    resolved_capabilities = (
        enabled_capabilities
        if enabled_capabilities is not None
        else state.get("enabled_capabilities", [])
    )

    current_version = framework_version()
    previous_version = state.get("framework_version", "unknown")

    registry = load_registry(TEMPLATE_ROOT)
    selections = validate_enabled_capabilities(resolved_capabilities, registry)
    capabilities = capability_selection(selections)
    candidates, _ = iter_template_files(include_structure=resolved_include_structure)

    # Build the template-side manifest (what the framework *wants* the host to have).
    template_manifest = _build_template_manifest(
        candidates, capabilities=capabilities, registry=registry
    )
    # Files that diverge from the template source after writing must use the
    # host's actual on-disk hash so tree_digest is comparable to state (ADR-FW-003).
    _patch_gitignore_hash(template_manifest, target, dry_run=False)
    _patch_host_file_hashes(template_manifest, target, APPEND_ONLY_FILES, dry_run=False)
    template_tree_digest = compute_tree_digest(template_manifest)

    # Normalise the stored manifest to map format (legacy list compatibility).
    state_manifest = _manifest_as_map(state.get("framework_manifest"))
    state_tree_digest = state.get("tree_digest", "")

    # Short-circuit: if the template tree hasn't changed AND no local drift,
    # skip the full traversal.  (ADR-FW-003: tree_digest replaces version as gate.)
    if not force and template_tree_digest == state_tree_digest:
        # Verify there is no local drift (host edited a file).
        locally_modified = _detect_local_modifications(target, state_manifest)
        if not locally_modified:
            return {
                "up_to_date": True,
                "framework_version": current_version,
                "previous_version": previous_version,
                "updated": [],
                "locally_modified": [],
                "conflicts": [],
                "skipped": [],
                "deleted": [],
                "gitignore_updates": [],
            }

    # Full traversal: classify each framework-owned file and act.
    updated: list[str] = []
    locally_modified_paths: list[str] = []
    conflicts: list[str] = []
    skipped: list[str] = []
    created_dirs: set[str] = set()

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for source_path in candidates:
        relative = source_path.relative_to(TEMPLATE_ROOT)
        relative_text = relative.as_posix()
        destination = target / relative

        if not is_framework_owned(relative):
            # Host-owned: copy only if missing and force, otherwise skip.
            if destination.exists() and not force:
                skipped.append(relative_text)
            else:
                updated.append(relative_text)
                _ensure_destination_parent(target, destination, created_dirs, dry_run)
                if not dry_run:
                    copy_template_file(
                        source_path,
                        destination,
                        relative=relative,
                        capabilities=capabilities,
                        registry=registry,
                    )
            continue

        ownership = template_manifest[relative_text]["ownership"]

        if ownership == OWNERSHIP_APPEND_ONLY:
            # Append-only: never overwrite; only merge missing entries.
            if not destination.exists():
                # File absent in host — copy it wholesale on first occurrence.
                updated.append(relative_text)
                _ensure_destination_parent(target, destination, created_dirs, dry_run)
                if not dry_run:
                    copy_template_file(
                        source_path,
                        destination,
                        relative=relative,
                        capabilities=capabilities,
                        registry=registry,
                    )
            else:
                added = merge_append_only_file(
                    source_path, destination, relative=relative, dry_run=dry_run
                )
                if added:
                    updated.append(relative_text)
            continue

        # Framework-owned (managed/generated): classify with three-way hash comparison.
        h_tpl = template_manifest[relative_text]["sha256"]
        state_entry = state_manifest.get(relative_text, {})
        h_state = state_entry.get("sha256")  # None for legacy/missing entries
        h_host = file_sha256(destination) if destination.exists() else None

        classification = _classify(h_host, h_state, h_tpl)

        if classification == "unchanged" and not force:
            # Nothing to do.
            continue

        if classification in ("updatable", "missing") or force:
            updated.append(relative_text)
            _ensure_destination_parent(target, destination, created_dirs, dry_run)
            if not dry_run:
                copy_template_file(
                    source_path,
                    destination,
                    relative=relative,
                    capabilities=capabilities,
                    registry=registry,
                )
        elif classification == "locally-modified":
            locally_modified_paths.append(relative_text)
        elif classification == "conflict":
            conflicts.append(relative_text)

    # Orphan cleanup: framework paths in old manifest no longer in template.
    old_manifest_keys = set(state_manifest)
    new_manifest_keys = set(template_manifest)
    orphan_paths = old_manifest_keys - new_manifest_keys

    deleted: list[str] = []
    for orphan in sorted(orphan_paths):
        if not is_framework_owned(Path(orphan)):
            continue
        orphan_file = target / orphan
        deleted.append(orphan)
        if not dry_run and orphan_file.exists():
            orphan_file.unlink()

    gitignore_updates = append_target_gitignore(target, dry_run=dry_run)

    # Patch on-disk hashes for files whose content diverges from the template source.
    _patch_gitignore_hash(template_manifest, target, dry_run=dry_run)
    _patch_host_file_hashes(template_manifest, target, APPEND_ONLY_FILES, dry_run=dry_run)
    template_tree_digest = compute_tree_digest(template_manifest)

    write_state(
        target,
        version=current_version,
        include_structure=resolved_include_structure,
        enabled_capabilities=selections,
        manifest=template_manifest,
        tree_digest=template_tree_digest,
        dry_run=dry_run,
    )

    return {
        "up_to_date": False,
        "framework_version": current_version,
        "previous_version": previous_version,
        "updated": updated,
        "locally_modified": locally_modified_paths,
        "conflicts": conflicts,
        "skipped": skipped,
        "deleted": deleted,
        "gitignore_updates": gitignore_updates,
    }


def _classify(
    h_host: str | None,
    h_state: str | None,
    h_tpl: str,
) -> str:
    """Classify a framework-owned file using the three-way hash comparison.

    Returns one of: unchanged / updatable / locally-modified / conflict / missing.
    """
    if h_host is None:
        return "missing"
    # Legacy state entry had no sha256; treat as needing update.
    if h_state is None:
        if h_host == h_tpl:
            return "unchanged"
        return "updatable"
    host_changed = h_host != h_state
    tpl_changed = h_tpl != h_state
    if not host_changed and not tpl_changed:
        return "unchanged"
    if not host_changed and tpl_changed:
        return "updatable"
    if host_changed and not tpl_changed:
        return "locally-modified"
    return "conflict"  # both changed


def _detect_local_modifications(
    target: Path, state_manifest: dict[str, dict]
) -> list[str]:
    """Return paths where the host file differs from its recorded sha256.

    Append-only files are excluded: they are expected to diverge from the
    template source because host entries may have been added.
    """
    modified = []
    for rel_text, entry in state_manifest.items():
        if entry.get("ownership") == OWNERSHIP_APPEND_ONLY:
            continue
        h_state = entry.get("sha256")
        if h_state is None:
            continue
        host_file = target / rel_text
        if not host_file.exists():
            continue
        if file_sha256(host_file) != h_state:
            modified.append(rel_text)
    return modified


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def print_summary(summary: dict, dry_run: bool) -> None:
    is_update = "previous_version" in summary
    if is_update:
        mode = "Dry run (update)" if dry_run else "Update"
        prev = summary.get("previous_version", "?")
        curr = summary.get("framework_version", "?")
        print(f"{mode} summary  [{prev} -> {curr}]")
        if summary.get("up_to_date"):
            print("Already up to date.")
            return

        updated = summary.get("updated", [])
        locally_modified = summary.get("locally_modified", [])
        conflicts = summary.get("conflicts", [])
        skipped = summary.get("skipped", [])
        deleted = summary.get("deleted", [])
        gitignore_updates = summary.get("gitignore_updates", [])

        print(f"- Updated (framework → host):        {len(updated)}")
        print(f"- Locally modified (preserved):      {len(locally_modified)}")
        print(f"- Conflict (host+framework changed):  {len(conflicts)}")
        print(f"- Skipped (host-owned):               {len(skipped)}")
        print(f"- Deleted (orphans):                  {len(deleted)}")
        print(f"- .gitignore entries added:           {len(gitignore_updates)}")

        for label, values in [
            ("Updated", updated),
            ("Locally modified (use --force to overwrite)", locally_modified),
            ("Conflict — host and template both changed (use --force to overwrite)", conflicts),
            ("Skipped (host-owned)", skipped),
            ("Deleted (orphans)", deleted),
            (".gitignore additions", gitignore_updates),
        ]:
            if not values:
                continue
            print(f"\n{label}:")
            for value in values:
                print(f"  {value}")

        if locally_modified or conflicts:
            print(
                "\nTip: run with --force to overwrite locally modified / conflicting files."
            )
    else:
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
            values = summary.get(key, [])
            if not values:
                continue
            print(f"\n{key.replace('_', ' ').title()}:")
            for value in values:
                print(f"  {value}")
