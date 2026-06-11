from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.runtime.project_profile import resolve_project_profile  # noqa: E402
from ai.runtime.skill_registry import build_skills_registry  # noqa: E402
from ai.tools.refresh_context import refresh_context  # noqa: E402
from scripts.run_uv_sync import run_update  # noqa: E402


def validate_consistency(project_root: Path) -> dict[str, list[str]]:
    registry = build_skills_registry(project_root)
    missing = [
        skill["path"]
        for skill in registry["skills"]
        if not (project_root / skill["path"]).exists()
    ]
    return {"missing": missing, "gated": []}


def restore_project(project_root: Path, *, dry_run: bool = False) -> dict[str, object]:
    project_root = project_root.resolve()
    resolved = resolve_project_profile(
        project_root,
        validate_dependencies=(project_root / "pyproject.toml").exists(),
    )

    if project_root == REPO_ROOT:
        run_update(dry_run=dry_run, resolved=resolved, python_path=None)
        dependencies: dict[str, object] = {"status": "ok"}
    else:
        dependencies = {"status": "skipped", "reason": "project_root != REPO_ROOT"}

    context = (
        {"status": "skipped", "reason": "dry-run"}
        if dry_run
        else refresh_context(project_root)
    )
    consistency = validate_consistency(project_root)

    return {
        "status": "ok",
        "profile_source": resolved.profile.source,
        "explicit_capabilities": list(resolved.explicit_capabilities),
        "implicit_capabilities": list(resolved.implicit_capabilities),
        "disabled_capabilities": list(resolved.disabled_capabilities),
        "invalid_capabilities": [],
        "dependencies": dependencies,
        "context": context,
        "consistency": consistency,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore a host from its active profile and capability registry."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        payload = restore_project(Path(args.project_root), dry_run=args.dry_run)
    except ValueError as exc:
        payload = {"status": "error", "error": str(exc)}
        print(json.dumps(payload, indent=2 if args.pretty else None))
        return 1

    print(json.dumps(payload, indent=2 if args.pretty else None))
    return 1 if payload["consistency"]["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
