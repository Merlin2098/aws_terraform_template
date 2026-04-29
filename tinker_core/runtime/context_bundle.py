from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tinker_core.runtime.skill_registry import build_skills_registry
from tinker_core.tools.inspect_project import inspect_project


RULES = [
    ".tinker/ is optional generated context and is never required at runtime.",
    "Keep execution explicit through existing scripts, Make targets, and direct Terraform commands.",
    "Skill files under ai/skills/ are guidance only and are not executable runtime logic.",
    "Infrastructure changes remain explicit and reviewed before terraform apply or destroy.",
]


def _project_purpose(project: dict[str, Any]) -> str:
    languages = project["project"].get("languages", [])
    providers = project["cloud"].get("providers", [])
    language_text = (
        ", ".join(languages[:-1])
        + (" and " + languages[-1] if len(languages) > 1 else languages[0])
        if languages
        else "software"
    )
    purpose = f"{language_text.capitalize()} project"
    if "data" in project["project"].get("project_types", []):
        purpose += " for data workflows"
    if providers:
        purpose += f" on {', '.join(provider.upper() for provider in providers)}"
    return purpose + "."


def build_context_bundle(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    project = inspect_project(project_root)
    skills_registry = build_skills_registry(project_root)
    skills = skills_registry.get("skills", [])

    domain_counts: dict[str, int] = {}
    for skill in skills:
        domain = str(skill.get("domain") or "general")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return {
        "project": {
            "name": project["project"]["name"],
            "purpose": _project_purpose(project),
        },
        "tech_stack": {
            "languages": project["project"]["languages"],
            "data_libraries": project["data_stack"]["libraries"],
            "cloud": project["cloud"]["providers"],
            "infra_tools": project["cloud"]["infra_tools"],
        },
        "structure": {
            "python": ["main.py", "src/", "scripts/"],
            "sql": ["src/transformations/"],
            "config": ["src/config/"],
            "contracts": ["src/contracts/"],
            "infrastructure": ["infra/"],
            "guidance": ["ai/skills.yaml", "ai/skills/"],
            "optional_context": [".tinker/"],
        },
        "entrypoints": project["entrypoints"],
        "core_modules": project["core_modules"],
        "skills_summary": {
            "count": len(skills),
            "domains": dict(sorted(domain_counts.items())),
        },
        "rules": RULES,
    }


def write_context_bundle(bundle: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(bundle, sort_keys=False, allow_unicode=False), encoding="utf-8"
    )


def build_and_persist_context_bundle(project_root: Path) -> dict[str, Any]:
    bundle = build_context_bundle(project_root)
    write_context_bundle(bundle, project_root / ".tinker" / "context_bundle.yaml")
    return bundle
