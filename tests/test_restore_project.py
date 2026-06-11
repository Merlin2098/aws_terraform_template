from __future__ import annotations

import json
from pathlib import Path

from scripts.restore_project import (
    gated_paths_to_exclude,
    restore_project,
    validate_consistency,
)


def _normalize_artifact(path: Path, content: str) -> str:
    """Strip volatile fields (e.g. ``generated_at`` timestamps) before comparing."""
    if path.suffix != ".json":
        return content
    payload = json.loads(content)
    payload.pop("generated_at", None)
    return json.dumps(payload, indent=2, sort_keys=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_sample_project(project_root: Path) -> None:
    _write(
        project_root / "ai" / "context.yaml",
        """artifacts:
  - .ai/context_bundle.yaml
  - .ai/skills_registry.json
  - .ai/dependencies_graph.json
  - .ai/treemap.md
  - llms.txt

ignore_dirs:
  - .ai
  - __pycache__

treemap_ignore_dirs:
  - .ai
  - __pycache__

ignore_top_level_files: []

structure:
  python:
    - src/
    - scripts/
  guidance:
    - ai/skills.yaml
    - ai/skills/
    - ai/context.yaml

rules:
  - .ai/ is optional generated context and is never required at runtime.

entrypoint_roots:
  directories:
    - scripts
    - src/jobs

module_roots:
  directories:
    - src
""",
    )
    _write(
        project_root / "ai" / "capabilities" / "business" / "saas.yaml",
        """name: saas
type: business

paths:
  - ai/skills/saas/
  - ai/domains/saas.md
""",
    )
    _write(
        project_root / "ai" / "skills.yaml",
        """example_skill:
  path: ai/skills/python/example.md
  description: Example skill

saas_auth:
  path: ai/skills/saas/auth.md
  description: SaaS auth skill
""",
    )
    _write(project_root / "ai" / "skills" / "python" / "example.md", "# Example\n")
    _write(project_root / "ai" / "skills" / "saas" / "auth.md", "# SaaS auth\n")
    _write(project_root / "src" / "jobs" / "example_job.py", "import json\n")
    _write(project_root / "scripts" / "helper.py", "print('ok')\n")


def test_gated_paths_to_exclude_without_saas(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    excluded = gated_paths_to_exclude(tmp_path, {})

    assert "ai/skills/saas/" in excluded
    assert "ai/domains/saas.md" in excluded


def test_gated_paths_to_exclude_with_saas(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    excluded = gated_paths_to_exclude(tmp_path, {"business": ["saas"]})

    assert excluded == set()


def test_validate_consistency_flags_gated_skill_without_capability(
    tmp_path: Path,
) -> None:
    _create_sample_project(tmp_path)

    result = validate_consistency(tmp_path, {})

    assert result["missing"] == []
    assert "ai/skills/saas/auth.md" in result["gated"]
    assert "ai/skills/python/example.md" not in result["gated"]


def test_validate_consistency_passes_when_capability_active(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    result = validate_consistency(tmp_path, {"business": ["saas"]})

    assert result["missing"] == []
    assert result["gated"] == []


def test_validate_consistency_flags_missing_skill_file(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)
    _write(
        tmp_path / "ai" / "skills.yaml",
        """ghost_skill:
  path: ai/skills/python/ghost.md
  description: Does not exist on disk
""",
    )

    result = validate_consistency(tmp_path, {})

    assert result["missing"] == ["ai/skills/python/ghost.md"]


def test_restore_project_dry_run_skips_context_and_dependencies(
    tmp_path: Path,
) -> None:
    _create_sample_project(tmp_path)
    _write(
        tmp_path / ".template-profile",
        "environment_profile=cloud\ncapability_profile=saas\n",
    )

    payload = restore_project(tmp_path, dry_run=True)

    assert payload["status"] == "ok"
    assert payload["environment_profile"] == "cloud"
    assert payload["package_manager"] is None
    assert payload["capabilities"] == {"business": ["saas"]}
    assert payload["active_capabilities"] == ["saas"]
    assert payload["dependencies"]["status"] == "skipped"
    assert payload["context"]["status"] == "skipped"
    assert payload["consistency"] == {"missing": [], "gated": []}


def test_restore_project_regenerates_context_artifacts(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)
    _write(
        tmp_path / ".template-profile",
        "environment_profile=local\ncapability_profile=saas\n",
    )

    payload = restore_project(tmp_path, dry_run=False)

    assert payload["context"]["status"] == "ok"
    for relative_path in payload["context"]["artifacts"]:
        assert (tmp_path / relative_path).exists()


def test_restore_project_is_idempotent(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)
    _write(
        tmp_path / ".template-profile",
        "environment_profile=local\ncapability_profile=saas\n",
    )

    first = restore_project(tmp_path, dry_run=False)
    snapshot = {
        path: _normalize_artifact(
            Path(path), (tmp_path / path).read_text(encoding="utf-8")
        )
        for path in first["context"]["artifacts"]
    }

    second = restore_project(tmp_path, dry_run=False)

    assert second["context"]["artifacts"] == first["context"]["artifacts"]
    for path in second["context"]["artifacts"]:
        content = (tmp_path / path).read_text(encoding="utf-8")
        assert _normalize_artifact(Path(path), content) == snapshot[path]


def test_restore_project_without_capability_block_uses_legacy_profile(
    tmp_path: Path,
) -> None:
    _create_sample_project(tmp_path)
    _write(
        tmp_path / ".template-profile",
        "package_manager=pip\nenvironment_profile=local\ncapability_profile=\n",
    )

    payload = restore_project(tmp_path, dry_run=True)

    assert payload["capabilities"] == {}
    assert payload["active_capabilities"] == []
    assert payload["consistency"]["gated"] == ["ai/skills/saas/auth.md"]
    assert "requirements*.txt" in payload["dependencies"]["warning"]
    assert "pip support has been retired" in payload["dependencies"]["warning"]
