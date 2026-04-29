from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.1.0"
DATA_LIBRARIES = {"awswrangler", "duckdb", "pandas", "polars", "pyarrow"}
IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tinker",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "docs",
    "node_modules",
    "tinker_core",
    "tinker_files",
    "venv",
}
IGNORED_TOP_LEVEL_FILES = {
    ".pre-commit-config.yaml",
}
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z0-9_\.]+)", re.MULTILINE)


def _safe_read(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _is_ignored(path: Path, project_root: Path) -> bool:
    relative = path.relative_to(project_root)
    if any(part in IGNORED_DIRS for part in relative.parts):
        return True
    if relative.parts and relative.parts[0] == "ai":
        return True
    if relative.name in IGNORED_TOP_LEVEL_FILES and len(relative.parts) == 1:
        return True
    if any(part.startswith(".") and part not in {".github"} for part in relative.parts):
        return True
    return False


def iter_project_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if _is_ignored(path, project_root):
            continue
        files.append(path)
    return files


def _rel(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def _detect_languages(project_root: Path, files: list[Path]) -> dict[str, Any]:
    counts = Counter()
    languages: set[str] = set()

    for path in files:
        suffix = path.suffix.lower()
        if path.name == "requirements.txt" or suffix == ".py":
            languages.add("python")
            counts["python"] += 1
        elif suffix == ".sql":
            languages.add("sql")
            counts["sql"] += 1
        elif suffix == ".tf":
            languages.add("terraform")
            counts["terraform"] += 1

    primary_language = None
    for candidate in ("python", "sql", "terraform"):
        if counts[candidate]:
            primary_language = candidate
            break

    project_types: set[str] = set()
    if primary_language == "python":
        project_types.add("automation")
    if counts["sql"] or (project_root / "src" / "transformations").exists():
        project_types.add("data")
    if counts["terraform"] or (project_root / "infra").exists():
        project_types.add("infrastructure")
    if not project_types:
        project_types.add("unknown")

    return {
        "project": {
            "name": project_root.name,
            "primary_language": primary_language,
            "languages": sorted(languages),
            "project_types": sorted(project_types),
        },
        "structure": {
            "has_tests": (project_root / "tests").exists(),
            "has_terraform": counts["terraform"] > 0
            or (project_root / "infra").exists(),
            "has_sql": counts["sql"] > 0,
            "has_guidance": (project_root / "ai" / "skills").exists(),
        },
    }


def _detect_data_stack(project_root: Path, files: list[Path]) -> dict[str, Any]:
    libraries: set[str] = set()
    patterns: set[str] = set()

    for path in files:
        rel_path = _rel(path, project_root)
        lower_rel = rel_path.lower()

        if path.suffix.lower() == ".sql":
            patterns.add("sql")
        if any(token in lower_rel for token in ("job", "pipeline", "etl", "transform")):
            patterns.add("etl")
        if any(token in lower_rel for token in ("contract", "validation", "quality")):
            patterns.add("data_quality")

        if (
            path.name not in {"requirements.txt", "pyproject.toml"}
            and path.suffix.lower() != ".py"
        ):
            continue

        text = _safe_read(path).lower()
        for library in DATA_LIBRARIES:
            if library in text:
                libraries.add(library)

    return {
        "data_stack": {
            "libraries": sorted(libraries),
            "patterns": sorted(patterns),
        }
    }


def _detect_cloud(project_root: Path, files: list[Path]) -> dict[str, Any]:
    providers: set[str] = set()
    infra_tools: set[str] = set()

    if (project_root / "infra").exists():
        infra_tools.add("terraform")

    for path in files:
        suffix = path.suffix.lower()
        if suffix not in {".py", ".tf", ".yaml", ".yml", ".json"} and path.name not in {
            "requirements.txt",
            "pyproject.toml",
        }:
            continue

        text = _safe_read(path).lower()
        if suffix == ".tf":
            infra_tools.add("terraform")
        if (
            'provider "aws"' in text
            or "arn:aws:" in text
            or "boto3" in text
            or "awswrangler" in text
        ):
            providers.add("aws")

    return {
        "cloud": {
            "providers": sorted(providers),
            "infra_tools": sorted(infra_tools),
        }
    }


def _entrypoints(project_root: Path) -> list[dict[str, str]]:
    entrypoints: list[dict[str, str]] = []

    main_path = project_root / "main.py"
    if main_path.exists():
        entrypoints.append({"type": "cli", "path": "main.py"})

    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        for path in sorted(scripts_dir.glob("*.py")):
            if path.name == "__init__.py":
                continue
            entrypoints.append(
                {"type": "script", "path": path.relative_to(project_root).as_posix()}
            )

    jobs_dir = project_root / "src" / "jobs"
    if jobs_dir.exists():
        for path in sorted(jobs_dir.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            entrypoints.append(
                {"type": "job", "path": path.relative_to(project_root).as_posix()}
            )

    return entrypoints


def _core_modules(project_root: Path) -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []

    main_path = project_root / "main.py"
    if main_path.exists():
        modules.append({"path": "main.py"})

    src_dir = project_root / "src"
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.py")):
            if path.name == "__init__.py":
                continue
            modules.append({"path": path.relative_to(project_root).as_posix()})

    return modules[:15]


def inspect_project(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    files = iter_project_files(project_root)
    language_info = _detect_languages(project_root, files)
    data_info = _detect_data_stack(project_root, files)
    cloud_info = _detect_cloud(project_root, files)

    return {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "project": language_info["project"],
        "structure": language_info["structure"],
        "data_stack": data_info["data_stack"],
        "cloud": cloud_info["cloud"],
        "entrypoints": _entrypoints(project_root),
        "core_modules": _core_modules(project_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a project for lightweight Tinker context signals."
    )
    parser.add_argument("--project-root", default=".", help="Project root to inspect.")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    args = parser.parse_args()

    payload = inspect_project(Path(args.project_root))
    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
