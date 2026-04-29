from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tinker_core.hooks.treemap import write_treemap
from tinker_core.runtime.context_bundle import build_and_persist_context_bundle
from tinker_core.runtime.dependency_graph import build_and_persist_dependency_graph
from tinker_core.runtime.skill_registry import build_and_persist_skills_registry


MANAGED_ARTIFACTS = {
    "light": [
        ".tinker/context_bundle.yaml",
        ".tinker/skills_registry.json",
    ],
    "full": [
        ".tinker/context_bundle.yaml",
        ".tinker/skills_registry.json",
        ".tinker/dependencies_graph.json",
        ".tinker/treemap.md",
    ],
}


def _warn(message: str) -> None:
    print(f"Tinker warning: {message}", file=sys.stderr)


def refresh_context(project_root: Path, *, full: bool = False) -> dict[str, object]:
    project_root = project_root.resolve()
    (project_root / ".tinker").mkdir(parents=True, exist_ok=True)

    build_and_persist_skills_registry(project_root)
    build_and_persist_context_bundle(project_root)

    artifacts = list(MANAGED_ARTIFACTS["light"])
    if full:
        build_and_persist_dependency_graph(project_root)
        write_treemap(project_root, project_root / ".tinker" / "treemap.md")
        artifacts = list(MANAGED_ARTIFACTS["full"])

    return {
        "status": "ok",
        "mode": "full" if full else "light",
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh optional Tinker context artifacts."
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
