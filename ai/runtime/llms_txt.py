from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.runtime.project_profile import ResolvedProfile, resolve_project_profile
from ai.runtime.skill_registry import build_skills_registry
from ai.tools.inspect_project import inspect_project


def _capability_lines(
    resolved: ResolvedProfile,
) -> list[str]:
    if not resolved.descriptors:
        return ["- (none active — see ai/capabilities/ for available capabilities)"]
    return [
        f"- {descriptor.name} ({descriptor.category}/{descriptor.type or 'unknown'})"
        for descriptor in sorted(
            resolved.descriptors, key=lambda item: (item.category, item.name)
        )
    ]


def _skill_lines(skills: list[dict[str, str]]) -> list[str]:
    if not skills:
        return ["- (no skills registered — see ai/skills.yaml)"]
    return [f"- {skill['path']}: {skill['description']}" for skill in skills]


def _spec_lines(project_root: Path) -> list[str]:
    specs_dir = project_root / "specs"
    if not specs_dir.is_dir():
        return ["- (no specs/ directory — local-profile host)"]

    lines: list[str] = []
    for subdir in ("template", "project"):
        target = specs_dir / subdir
        if not target.is_dir():
            continue
        for path in sorted(target.rglob("*.md")):
            lines.append(f"- {path.relative_to(project_root).as_posix()}")

    return lines or ["- (specs/ directory present but empty)"]


def build_llms_txt(
    project_root: Path,
    *,
    project: dict[str, Any] | None = None,
    skills_registry: dict[str, Any] | None = None,
    resolved: ResolvedProfile | None = None,
) -> str:
    """Build the contents of ``llms.txt``.

    Per ``docs/prompt/upgrade.md`` §5, ``llms.txt`` provides a project
    summary, architecture summary, current capabilities, relevant
    specifications, and agent onboarding pointers — generated from project
    inspection, the capability registry, and the skills registry.
    """
    project_root = project_root.resolve()
    project = project or inspect_project(project_root)
    resolved = resolved or resolve_project_profile(
        project_root, validate_dependencies=False
    )
    skills_registry = skills_registry or build_skills_registry(
        project_root, resolved=resolved
    )

    languages = project["project"].get("languages", []) or ["unknown"]
    cloud_providers = project["cloud"].get("providers", []) or ["none"]
    infra_tools = project["cloud"].get("infra_tools", []) or ["none"]

    lines = [
        "# Project AI Guide",
        "",
        "> Generic instructions and discovered context for the current project.",
        "",
        "Use the repository contents and active capability profile as the source "
        "of truth. Do not infer behavior from the repository name.",
        "",
        "## Architecture",
        "",
        f"- languages: {', '.join(languages)}",
        f"- cloud: {', '.join(cloud_providers)}",
        f"- infrastructure: {', '.join(infra_tools)}",
        "",
        "## Capabilities",
        "",
        *_capability_lines(resolved),
        "",
        "## Skills / Guidance",
        "",
        *_skill_lines(skills_registry.get("skills", [])),
        "",
        "## Relevant Specs",
        "",
        *_spec_lines(project_root),
        "",
        "## Agent Onboarding",
        "",
        "- Start with AGENTS.md for the agent contract and skill trigger map.",
        "- ai/context.yaml is the authoritative AI context-generation config.",
        "- ai/domains/index.md provides domain-based navigation across skills.",
        "- .ai/ contains generated context artifacts (optional, never required at runtime).",
        "",
    ]

    return "\n".join(lines)


def write_llms_txt(content: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_and_persist_llms_txt(
    project_root: Path,
    output_path: Path,
    *,
    project: dict[str, Any] | None = None,
    skills_registry: dict[str, Any] | None = None,
    resolved: ResolvedProfile | None = None,
) -> str:
    content = build_llms_txt(
        project_root,
        project=project,
        skills_registry=skills_registry,
        resolved=resolved,
    )
    write_llms_txt(content, output_path)
    return content
