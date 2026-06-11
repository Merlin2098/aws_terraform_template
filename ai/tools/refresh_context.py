from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai.hooks.treemap import write_treemap
from ai.runtime.config import artifact_paths, load_context_config
from ai.runtime.context_bundle import build_and_persist_context_bundle
from ai.runtime.dependency_graph import build_and_persist_dependency_graph
from ai.runtime.llms_txt import build_and_persist_llms_txt
from ai.runtime.skill_registry import build_and_persist_skills_registry
from ai.tools.inspect_project import inspect_project


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

    build_and_persist_dependency_graph(
        project_root,
        _artifact_path(project_root, artifact_strings, "dependencies_graph.json"),
    )

    llms_txt_path = _artifact_path(
        project_root, artifact_strings, "llms.txt", required=False
    )
    if llms_txt_path is not None:
        build_and_persist_llms_txt(
            project_root,
            llms_txt_path,
            project=project,
            skills_registry=skills_registry,
        )

    write_treemap(
        project_root, _artifact_path(project_root, artifact_strings, "treemap.md")
    )

    return {
        "status": "ok",
        "mode": "full",
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
