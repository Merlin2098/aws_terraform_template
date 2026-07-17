from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_skills(args: argparse.Namespace) -> int:
    from agents_framework import framework_root
    from agents_framework.runtime.skill_registry import build_skills_registry
    from agents_framework.runtime.project_profile import resolve_project_profile

    project_root = Path(args.project_root).resolve()
    try:
        resolved = resolve_project_profile(project_root, validate_dependencies=False)
        registry = build_skills_registry(project_root, resolved=resolved)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    skills = registry.get("skills", [])
    match_term = args.match.lower() if args.match else None
    if match_term:
        skills = [
            s for s in skills
            if match_term in s.get("name", "").lower()
            or match_term in s.get("description", "").lower()
            or match_term in s.get("domain", "").lower()
        ]

    if args.json:
        print(json.dumps({"skills": skills}, indent=2, ensure_ascii=False))
    else:
        if not skills:
            print("No matching skills found.")
        else:
            fw = framework_root()
            for skill in skills:
                path_text = skill.get("path", "")
                abs_path = fw / path_text if path_text else None
                desc = skill.get("description", "")
                print(f"  {skill['name']:30s}  [{skill['domain']}]  {desc}")
                if abs_path and abs_path.exists():
                    print(f"    => {abs_path}")
    return 0


def _cmd_policy(args: argparse.Namespace) -> int:
    from agents_framework import framework_root
    from agents_framework.runtime.project_profile import resolve_project_profile

    project_root = Path(args.project_root).resolve()

    if args.active:
        try:
            resolved = resolve_project_profile(project_root, validate_dependencies=False)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        active_caps = set(resolved.active_capabilities)
        print(f"Active capabilities: {', '.join(sorted(active_caps)) or 'none'}")

    # Always show global.md
    policy_path = framework_root() / "policies" / "global.md"
    if policy_path.exists():
        print(f"\nGlobal policies: {policy_path}")
        if args.show:
            print(policy_path.read_text(encoding="utf-8"))
    return 0


def _cmd_context(args: argparse.Namespace) -> int:
    from agents_framework.tools.refresh_context import refresh_context

    if args.repo:
        project_root = Path(args.repo).resolve()
    else:
        project_root = Path(args.project_root).resolve()

    try:
        result = refresh_context(project_root)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_deps_check(args: argparse.Namespace) -> int:
    """Advisory: compare host requirements/package.json vs active capability extras."""
    if args.repo:
        project_root = Path(args.repo).resolve()
    else:
        project_root = Path(args.project_root).resolve()

    try:
        from agents_framework.runtime.project_profile import (
            resolve_project_profile,
            pip_install_args,
        )
        resolved = resolve_project_profile(project_root, validate_dependencies=False)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    manager = resolved.profile.dependency_policy.manager
    extras = list(resolved.extras)
    print(f"Dependency manager: {manager}")
    print(f"Active capability extras: {extras or '(none)'}")

    if manager == "pip":
        req_file = project_root / "requirements.txt"
        if req_file.exists():
            print(f"\nHost requirements.txt: {req_file}")
            print("(advisory: capability extras map to pyproject optional-deps,")
            print(" not requirements.txt lines — this check is informational)")
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            print(f"\nHost pyproject.toml: {pyproject}")
            install_args = pip_install_args(resolved)
            print(f"Suggested install: pip {' '.join(install_args)}")
    elif manager == "npm":
        pkg = project_root / "package.json"
        if pkg.exists():
            print(f"\nHost package.json: {pkg}")
            print("(framework capabilities do not map to npm packages)")
    elif manager == "uv":
        from agents_framework.runtime.project_profile import uv_sync_args
        sync_args = uv_sync_args(resolved)
        print(f"Suggested sync: uv {' '.join(sync_args)}")
    return 0


def _cmd_ai_refresh(args: argparse.Namespace) -> int:
    from agents_framework.tools.refresh_context import main as refresh_main
    sys.argv = ["agents-framework", "--project-root", args.project_root]
    if args.pretty:
        sys.argv.append("--pretty")
    return refresh_main()


def _cmd_sync_deps(args: argparse.Namespace) -> int:
    from agents_framework.tools.sync_deps import main as sync_main
    project_root = Path(args.project_root).resolve()
    try:
        sync_main(project_root)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_workspace_status(args: argparse.Namespace) -> int:
    from agents_framework.workspace import workspace_status

    workspace_root = Path(args.workspace_root).resolve()
    try:
        status = workspace_status(workspace_root)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Workspace: {status['workspace']}")
    print(f"Framework: {status['framework_source'] or '(not set)'}")
    print(f"\nMembers ({len(status['members'])}):")
    for m in status["members"]:
        attached = "✓" if m["attached"] else "✗"
        index = "✓" if m["ai_index_exists"] else "–"
        print(
            f"  {attached} attached  {index} .ai/  [{m['deps_manager']:4s}]  {m['name']}"
        )
    return 0


def _cmd_workspace_attach(args: argparse.Namespace) -> int:
    from agents_framework.workspace import workspace_attach

    workspace_root = Path(args.workspace_root).resolve()
    repo_path = Path(args.repo).resolve()
    capabilities = args.enable or []

    result = workspace_attach(
        workspace_root,
        repo_path,
        deps_manager=args.manager,
        capabilities=capabilities,
        framework_source=args.framework_source or "",
        dry_run=args.dry_run,
    )

    mode = "Dry run — " if args.dry_run else ""
    print(f"{mode}Attached: {result['attached']}")
    for written in result["written"]:
        print(f"  wrote: {written}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agents-framework",
        description="Workspace Framework CLI — manage multi-repo AI guidance.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Host repository root (default: current directory).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # skills
    p_skills = subparsers.add_parser("skills", help="List framework skills.")
    p_skills.add_argument("--match", help="Filter skills by keyword.")
    p_skills.add_argument("--json", action="store_true", help="Output as JSON.")

    # policy
    p_policy = subparsers.add_parser("policy", help="Show framework policies.")
    p_policy.add_argument(
        "--active", action="store_true", help="Show only active-capability policies."
    )
    p_policy.add_argument("--show", action="store_true", help="Print policy content.")

    # context
    p_context = subparsers.add_parser(
        "context", help="Regenerate .ai/ context index for a repo."
    )
    p_context.add_argument("--repo", help="Path to the target repo (overrides --project-root).")

    # deps
    p_deps = subparsers.add_parser(
        "deps", help="Advisory dependency check (does not modify host deps)."
    )
    p_deps.add_argument("--check", action="store_true", help="Run advisory check.")
    p_deps.add_argument("--repo", help="Path to the target repo.")

    # ai-refresh
    p_refresh = subparsers.add_parser("ai-refresh", help="Refresh AI context artifacts.")
    p_refresh.add_argument("--pretty", action="store_true")

    # sync-deps
    p_sync = subparsers.add_parser(
        "sync-deps", help="Sync host venv based on active capabilities."
    )

    # workspace
    p_ws = subparsers.add_parser("workspace", help="Workspace-level commands.")
    ws_subs = p_ws.add_subparsers(dest="ws_command", required=True)

    p_ws_status = ws_subs.add_parser("status", help="Show workspace member status.")
    p_ws_status.add_argument(
        "--workspace-root", default=".", help="Workspace root directory."
    )

    p_ws_attach = ws_subs.add_parser("attach", help="Attach a repo to the framework.")
    p_ws_attach.add_argument("repo", help="Path to the repo to attach.")
    p_ws_attach.add_argument(
        "--workspace-root", default=".", help="Workspace root directory."
    )
    p_ws_attach.add_argument(
        "--manager",
        default="pip",
        choices=["pip", "uv", "npm"],
        help="Host dependency manager.",
    )
    p_ws_attach.add_argument(
        "--enable",
        action="append",
        metavar="CATEGORY:NAME",
        help="Enable a capability (repeat for multiple).",
    )
    p_ws_attach.add_argument(
        "--framework-source", default="", help="Framework source path or git URL."
    )
    p_ws_attach.add_argument(
        "--dry-run", action="store_true", help="Preview without writing files."
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "skills":
        return _cmd_skills(args)
    if args.command == "policy":
        return _cmd_policy(args)
    if args.command == "context":
        return _cmd_context(args)
    if args.command == "deps":
        return _cmd_deps_check(args)
    if args.command == "ai-refresh":
        return _cmd_ai_refresh(args)
    if args.command == "sync-deps":
        return _cmd_sync_deps(args)
    if args.command == "workspace":
        if args.ws_command == "status":
            return _cmd_workspace_status(args)
        if args.ws_command == "attach":
            return _cmd_workspace_attach(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
