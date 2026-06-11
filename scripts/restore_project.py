from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.runtime.capability_registry import (  # noqa: E402
    load_registry,
    resolve_descriptors,
)
from ai.runtime.profile import (  # noqa: E402
    DEFAULT_ENVIRONMENT_PROFILE,
    load_profile,
)
from ai.runtime.skill_registry import build_skills_registry  # noqa: E402
from ai.tools.refresh_context import refresh_context  # noqa: E402
from scripts.run_uv_sync import run_update  # noqa: E402


def gated_paths_to_exclude(
    project_root: Path, capabilities: dict[str, list[str]]
) -> set[str]:
    """Paths owned by an unselected ``business`` capability.

    Mirrors ``ai/installer.py``'s registry-driven exclusion (SPEC-FW-007) so
    restore validates a host against the same rule install applies.
    """
    from ai.installer import CAPABILITY_GATED_CATEGORY
    from ai.runtime.capability_registry import active_paths, category_paths

    registry = load_registry(project_root)
    all_gated = category_paths(registry, CAPABILITY_GATED_CATEGORY)
    active = active_paths(resolve_descriptors(registry, capabilities))
    return all_gated - active


def sync_dependencies(
    *, package_manager: str | None, environment_profile: str | None, dry_run: bool
) -> dict[str, object]:
    """Step 4: sync dependencies for uv hosts.

    pip hosts manage `requirements*.txt` manually (per ADR-FW-002, pip is
    legacy) — restore does not run `run_pip_init.py` since it has no
    update/lock equivalent to keep idempotent.
    """
    if package_manager != "uv":
        return {"status": "skipped", "reason": f"package_manager={package_manager!r}"}

    run_update(
        dry_run=dry_run,
        profile=environment_profile or DEFAULT_ENVIRONMENT_PROFILE,
        use_dev_dependencies=True,
        python_path=None,
    )
    return {"status": "ok"}


def validate_consistency(
    project_root: Path, capabilities: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Step 8: every `ai/skills.yaml` entry must point at an existing file that
    is not owned by an unselected (gated) capability.

    Extends SPEC-FW-003's invariant per SPEC-FW-009's validation criteria.
    """
    excluded = gated_paths_to_exclude(project_root, capabilities)
    registry = build_skills_registry(project_root)

    missing: list[str] = []
    gated: list[str] = []

    for skill in registry["skills"]:
        path = skill["path"]
        if not (project_root / path).exists():
            missing.append(path)
            continue
        for excluded_path in excluded:
            excluded_path = excluded_path.rstrip("/")
            if path == excluded_path or path.startswith(excluded_path + "/"):
                gated.append(path)
                break

    return {"missing": missing, "gated": gated}


def restore_project(project_root: Path, *, dry_run: bool = False) -> dict[str, object]:
    project_root = project_root.resolve()
    profile_file = project_root / ".template-profile"

    # Steps 1-2: read the active profile and normalize legacy fields.
    profile = load_profile(profile_file)

    # Step 3: resolve active capability descriptors.
    registry = load_registry(project_root)
    descriptors = resolve_descriptors(registry, profile.capabilities)

    # Step 4: sync dependencies. `run_uv_sync` always operates on the
    # repository containing this script, so syncing a different
    # `--project-root` is not supported.
    if project_root == REPO_ROOT:
        dependencies = sync_dependencies(
            package_manager=profile.package_manager,
            environment_profile=profile.environment_profile,
            dry_run=dry_run,
        )
    else:
        dependencies = {"status": "skipped", "reason": "project_root != REPO_ROOT"}

    # Steps 5-7: regenerate skills registry, .ai/ artifacts, and llms.txt.
    # `refresh_context` (SPEC-FW-010) regenerates `llms.txt` alongside the
    # other artifacts when it is listed in `ai/context.yaml`'s `artifacts:`.
    if dry_run:
        context = {"status": "skipped", "reason": "dry-run"}
    else:
        context = refresh_context(project_root)

    # Step 8: validate consistency.
    consistency = validate_consistency(project_root, profile.capabilities)

    return {
        "status": "ok",
        "environment_profile": profile.environment_profile,
        "package_manager": profile.package_manager,
        "capabilities": profile.capabilities,
        "active_capabilities": [descriptor.name for descriptor in descriptors],
        "dependencies": dependencies,
        "context": context,
        "consistency": consistency,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore a host project to a consistent state from its "
        ".template-profile and capability registry."
    )
    parser.add_argument("--project-root", default=".", help="Project root to restore.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip dependency sync and artifact regeneration; report only.",
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    args = parser.parse_args()

    payload = restore_project(Path(args.project_root), dry_run=args.dry_run)

    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))

    if payload["consistency"]["missing"] or payload["consistency"]["gated"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
