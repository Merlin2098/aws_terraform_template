from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai.hooks.treemap import write_treemap
from ai.runtime.config import artifacts_for_mode, load_context_config
from ai.runtime.context_bundle import build_and_persist_context_bundle
from ai.runtime.dependency_graph import build_and_persist_dependency_graph
from ai.runtime.skill_registry import build_and_persist_skills_registry
from ai.tools.inspect_project import inspect_project


def _warn(message: str) -> None:
    print(f"AI warning: {message}", file=sys.stderr)


def _artifact_path(
    project_root: Path, artifact_strings: list[str], filename: str
) -> Path:
    for artifact in artifact_strings:
        path = Path(artifact)
        if path.name == filename:
            return project_root / path
    raise ValueError(f"Missing artifact path for {filename}")


def refresh_context(project_root: Path, *, full: bool = False) -> dict[str, object]:
    project_root = project_root.resolve()
    config = load_context_config(project_root)
    artifact_strings = artifacts_for_mode(config, full=full)
    project = inspect_project(project_root)

    skills_registry = build_and_persist_skills_registry(
        project_root,
        _artifact_path(project_root, artifact_strings, "skills_registry.json"),
    )
    build_and_persist_context_bundle(
        project_root,
        _artifact_path(project_root, artifact_strings, "context_bundle.yaml"),
        project=project,
        skills_registry=skills_registry,
    )

    if full:
        build_and_persist_dependency_graph(
            project_root,
            _artifact_path(project_root, artifact_strings, "dependencies_graph.json"),
        )
        write_treemap(
            project_root, _artifact_path(project_root, artifact_strings, "treemap.md")
        )

    return {
        "status": "ok",
        "mode": "full" if full else "light",
        "artifacts": artifact_strings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh optional AI context artifacts."
    )
    parser.add_argument("--project-root", default=".", help="Project root to refresh.")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--light", action="store_true", help="Generate the lightweight context set."
    )
    mode.add_argument(
        "--full", action="store_true", help="Generate the full optional context set."
    )
    args = parser.parse_args()

    full_mode = args.full
    try:
        payload = refresh_context(Path(args.project_root), full=full_mode)
    except Exception as exc:
        if full_mode:
            _warn(str(exc))
            return 1
        _warn(str(exc))
        return 0

    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
