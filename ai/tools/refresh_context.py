from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai.hooks.treemap import write_treemap
from ai.runtime.config import artifact_paths, load_context_config
from ai.runtime.context_bundle import build_and_persist_context_bundle
from ai.runtime.dependency_graph import build_and_persist_dependency_graph
from ai.runtime.skill_registry import (
    build_and_persist_skills_registry,
    build_skills_registry,
)
from ai.tools.inspect_project import inspect_project
from ai.runtime.project_profile import resolve_project_profile


def _warn(message: str) -> None:
    print(f"AI warning: {message}", file=sys.stderr)


def _artifact_path(
    project_root: Path,
    artifact_strings: list[str],
    filename: str,
    *,
    required: bool = True,
) -> Path | None:
    for artifact in artifact_strings:
        path = Path(artifact)
        if path.name == filename:
            return project_root / path
    if required:
        raise ValueError(f"Missing artifact path for {filename}")
    return None


def refresh_context(project_root: Path) -> dict[str, object]:
    project_root = project_root.resolve()
    config = load_context_config(project_root)
    artifact_strings = artifact_paths(config)
    project = inspect_project(project_root)
    resolved = resolve_project_profile(project_root, validate_dependencies=False)
    active_artifacts = set(resolved.artifacts)
    if resolved.profile.source != "yaml" and not active_artifacts:
        active_artifacts = {
            "skills_registry",
            "context_bundle",
            "dependency_graph",
        }

    generated: list[str] = []
    if "skills_registry" in active_artifacts:
        skills_path = _artifact_path(
            project_root, artifact_strings, "skills_registry.json"
        )
        skills_registry = build_and_persist_skills_registry(
            project_root,
            skills_path,
            resolved=resolved,
        )
        generated.append(skills_path.relative_to(project_root).as_posix())
    else:
        skills_registry = build_skills_registry(project_root, resolved=resolved)

    if "context_bundle" in active_artifacts:
        context_path = _artifact_path(
            project_root, artifact_strings, "context_bundle.yaml"
        )
        build_and_persist_context_bundle(
            project_root,
            context_path,
            project=project,
            skills_registry=skills_registry,
            resolved=resolved,
        )
        generated.append(context_path.relative_to(project_root).as_posix())

    if "dependency_graph" in active_artifacts:
        graph_path = _artifact_path(
            project_root, artifact_strings, "dependencies_graph.json"
        )
        build_and_persist_dependency_graph(project_root, graph_path)
        generated.append(graph_path.relative_to(project_root).as_posix())

    treemap_path = _artifact_path(project_root, artifact_strings, "treemap.md")
    write_treemap(project_root, treemap_path)
    generated.append(treemap_path.relative_to(project_root).as_posix())

    return {
        "status": "ok",
        "mode": "full",
        "artifacts": generated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh optional AI context artifacts."
    )
    parser.add_argument("--project-root", default=".", help="Project root to refresh.")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    args = parser.parse_args()

    try:
        payload = refresh_context(Path(args.project_root))
    except Exception as exc:
        _warn(str(exc))
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
