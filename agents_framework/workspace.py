from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


WORKSPACE_FILENAME = "workspace.yaml"


def _load_workspace(workspace_root: Path) -> dict[str, Any]:
    path = workspace_root / WORKSPACE_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"No {WORKSPACE_FILENAME} found in {workspace_root}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Invalid {WORKSPACE_FILENAME}: must be a mapping.")
    return loaded


def workspace_status(workspace_root: Path) -> dict[str, Any]:
    """Return a status summary of all workspace members."""
    workspace_root = workspace_root.resolve()
    config = _load_workspace(workspace_root)
    members = config.get("members") or []
    results: list[dict[str, Any]] = []

    for member in members:
        member_path = workspace_root / member["path"]
        has_attachment = (member_path / ".agents-framework.yaml").exists()
        ai_index = member_path / ".ai"
        results.append(
            {
                "name": member.get("name", member["path"]),
                "path": member["path"],
                "deps_manager": member.get("deps_manager", "unknown"),
                "attached": has_attachment,
                "ai_index_exists": ai_index.is_dir(),
            }
        )

    return {
        "workspace": config.get("workspace", {}).get("name", workspace_root.name),
        "framework_source": config.get("framework", {}).get("source", ""),
        "members": results,
    }


def workspace_attach(
    workspace_root: Path,
    repo_path: Path,
    *,
    deps_manager: str = "pip",
    capabilities: list[str] | None = None,
    framework_source: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Attach a repo to the workspace framework.

    Creates ``.agents-framework.yaml`` in the target repo and appends a
    pointer block to its ``CLAUDE.md`` (if present).  Does not copy any
    framework files into the repo.
    """
    repo_path = repo_path.resolve()
    profile_path = repo_path / ".agents-framework.yaml"
    enabled = capabilities or []

    profile_doc: dict[str, Any] = {
        "schema_version": 2,
        "capabilities": {"enabled": enabled},
        "precedence": {
            "conventions": "host-first",
            "safety": "framework-required",
        },
        "overrides": {"skills": {}, "policies": {}},
        "dependencies": {
            "manager": deps_manager,
            "authority": "host",
            "include_dev": True,
            "additional_extras": [],
        },
    }
    if framework_source:
        profile_doc["framework"] = {"source": framework_source}

    pointer_block = (
        "\n\n## Agents Framework (referenced, not copied)\n\n"
        "Patterns and policies come from `agents_framework`, installed via\n"
        "`pip install -e vendor/agents-framework` (Python) or\n"
        "`pipx install ./vendor/agents-framework` (Node/CLI).\n\n"
        "**This CLAUDE.md and any repo AGENTS.md always take precedence**\n"
        "over framework guidance (Axis A of the precedence hierarchy).\n\n"
        "- Active capabilities: see `.agents-framework.yaml`\n"
        "- List skills: `agents-framework skills --match \"<task>\"`\n"
        "- List active policies: `agents-framework policy --active`\n"
        "- Regenerate index: `agents-framework ai-refresh`\n"
    )

    written: list[str] = []

    if not dry_run:
        profile_path.write_text(
            yaml.safe_dump(profile_doc, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )
    written.append(str(profile_path.relative_to(workspace_root)))

    claude_md = repo_path / "CLAUDE.md"
    if claude_md.exists():
        existing = claude_md.read_text(encoding="utf-8")
        if "Agents Framework (referenced" not in existing:
            if not dry_run:
                claude_md.write_text(existing.rstrip() + pointer_block, encoding="utf-8")
            written.append(str(claude_md.relative_to(workspace_root)))
    else:
        if not dry_run:
            claude_md.write_text(
                f"# {repo_path.name}\n{pointer_block}", encoding="utf-8"
            )
        written.append(str(claude_md.relative_to(workspace_root)))

    # Ensure .ai/ is gitignored
    gitignore = repo_path / ".gitignore"
    ai_entry = ".ai/"
    if gitignore.exists():
        existing_gi = gitignore.read_text(encoding="utf-8")
        if ai_entry not in existing_gi.splitlines():
            if not dry_run:
                sep = "\n" if existing_gi.endswith("\n") else "\n\n"
                gitignore.write_text(
                    existing_gi + sep + ai_entry + "\n", encoding="utf-8"
                )
            written.append(str(gitignore.relative_to(workspace_root)) + " (+.ai/)")
    else:
        if not dry_run:
            gitignore.write_text(ai_entry + "\n", encoding="utf-8")
        written.append(str(gitignore.relative_to(workspace_root)))

    return {"attached": str(repo_path), "written": written, "dry_run": dry_run}
