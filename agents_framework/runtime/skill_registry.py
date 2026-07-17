from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from agents_framework import framework_root
from agents_framework.runtime.capability_registry import active_paths, load_registry
from agents_framework.runtime.project_profile import ResolvedProfile, resolve_project_profile


def _infer_domain(path_text: str, fallback: str = "general") -> str:
    parts = Path(path_text).as_posix().split("/")
    # Handles both "ai/skills/domain/file.md" and "skills/domain/file.md"
    for i, part in enumerate(parts):
        if part == "skills" and i + 1 < len(parts):
            return parts[i + 1]
    if len(parts) >= 2:
        return parts[-2]
    return fallback


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _short_description_from_markdown(path: Path) -> str:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        return line
    return ""


def _registry_from_yaml(index_path: Path, skills_root: Path) -> list[dict[str, str]]:
    loaded = _load_yaml(index_path)
    skills: list[dict[str, str]] = []

    for name, value in sorted(loaded.items()):
        if not isinstance(value, dict):
            continue
        path_text = str(value.get("path", "")).strip()
        if not path_text:
            continue
        skills.append(
            {
                "name": str(name).strip(),
                "domain": str(value.get("domain") or _infer_domain(path_text)).strip(),
                "path": Path(path_text).as_posix(),
                "description": str(value.get("description", "")).strip(),
            }
        )

    return skills


def _registry_from_scan(skills_root: Path) -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    if not skills_root.exists():
        return skills

    for path in sorted(skills_root.rglob("*.md")):
        relative = path.relative_to(skills_root.parent).as_posix()
        skills.append(
            {
                "name": path.stem,
                "domain": _infer_domain(relative, fallback=path.parent.name),
                "path": relative,
                "description": _short_description_from_markdown(path),
            }
        )

    return skills


def _path_matches(path_text: str, prefix: str) -> bool:
    normalized = prefix.rstrip("/")
    return path_text == normalized or path_text.startswith(normalized + "/")


def _filter_active_skills(
    skills: list[dict[str, str]],
    resolved: ResolvedProfile,
) -> list[dict[str, str]]:
    registry = load_registry()
    owned_paths = active_paths(
        [
            descriptor
            for category in registry.values()
            for descriptor in category.values()
        ]
    )
    active = set(resolved.paths)
    filtered: list[dict[str, str]] = []
    for skill in skills:
        path_text = skill["path"]
        owners = [prefix for prefix in owned_paths if _path_matches(path_text, prefix)]
        if not owners or any(prefix in active for prefix in owners):
            filtered.append(skill)
    return filtered


def build_skills_registry(
    project_root: Path, *, resolved: ResolvedProfile | None = None
) -> dict[str, Any]:
    fw_root = framework_root()
    index_path = fw_root / "skills.yaml"
    skills_root = fw_root / "skills"

    if index_path.exists():
        skills = _registry_from_yaml(index_path, skills_root)
    else:
        skills = _registry_from_scan(skills_root)

    resolved = resolved or resolve_project_profile(
        project_root, validate_dependencies=False
    )
    skills = _filter_active_skills(skills, resolved)

    # Resolve relative framework paths to absolute so skills are readable from any host repo.
    # framework_root() returns agents_template/ai/ in dev mode; skill paths in skills.yaml
    # are relative to agents_template/ (one level up).
    package_root = fw_root.parent
    for skill in skills:
        candidate = (package_root / skill["path"]).resolve()
        if candidate.exists():
            skill["abs_path"] = candidate.as_posix()

    return {"skills": skills}


def write_skills_registry(registry: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_and_persist_skills_registry(
    project_root: Path,
    output_path: Path,
    *,
    resolved: ResolvedProfile | None = None,
) -> dict[str, Any]:
    registry = build_skills_registry(project_root, resolved=resolved)
    write_skills_registry(registry, output_path)
    return registry
