from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def _infer_domain(path_text: str, fallback: str = "general") -> str:
    parts = Path(path_text).as_posix().split("/")
    if len(parts) >= 3 and parts[0] == "ai" and parts[1] == "skills":
        return parts[2]
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


def _registry_from_yaml(index_path: Path) -> list[dict[str, str]]:
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


def _registry_from_scan(skills_root: Path, project_root: Path) -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []
    if not skills_root.exists():
        return skills

    for path in sorted(skills_root.rglob("*.md")):
        relative = path.relative_to(project_root).as_posix()
        skills.append(
            {
                "name": path.stem,
                "domain": _infer_domain(relative, fallback=path.parent.name),
                "path": relative,
                "description": _short_description_from_markdown(path),
            }
        )

    return skills


def build_skills_registry(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    index_path = project_root / "ai" / "skills.yaml"
    skills_root = project_root / "ai" / "skills"

    if index_path.exists():
        skills = _registry_from_yaml(index_path)
    else:
        skills = _registry_from_scan(skills_root, project_root)

    return {"skills": skills}


def write_skills_registry(registry: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_and_persist_skills_registry(
    project_root: Path, output_path: Path
) -> dict[str, Any]:
    registry = build_skills_registry(project_root)
    write_skills_registry(registry, output_path)
    return registry
