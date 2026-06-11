from __future__ import annotations

import json
from pathlib import Path

from scripts.restore_project import restore_project, validate_consistency


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_sample_project(project_root: Path, *, enable_saas: bool = True) -> None:
    _write(
        project_root / "pyproject.toml",
        """
[project]
name = "sample"
version = "0.1.0"
dependencies = []
[project.optional-dependencies]
local = []
saas = []
[dependency-groups]
dev-local = []
""",
    )
    _write(
        project_root / "ai/context.yaml",
        """
artifacts:
  - .ai/context_bundle.yaml
  - .ai/skills_registry.json
  - .ai/dependencies_graph.json
  - .ai/treemap.md
  - llms.txt
ignore_dirs: [.ai, __pycache__]
treemap_ignore_dirs: [.ai, __pycache__]
ignore_top_level_files: []
structure: {}
rules: []
entrypoint_roots:
  directories: [src]
module_roots:
  directories: [src]
""",
    )
    _write(
        project_root / "ai/capabilities/languages/python.yaml",
        """
name: python
paths: [ai/skills/python/]
dependencies:
  extras: [local]
  groups: [dev-local]
scanners: [python]
artifacts: [dependency_graph, context_bundle, skills_registry]
""",
    )
    _write(
        project_root / "ai/capabilities/frameworks/react.yaml",
        "name: react\ndepends_on:\n  languages: [python]\n",
    )
    _write(
        project_root / "ai/capabilities/business/saas.yaml",
        """
name: saas
depends_on:
  frameworks: [react]
paths: [ai/skills/saas/]
dependencies:
  extras: [saas]
artifacts: [context_bundle]
""",
    )
    _write(
        project_root / "ai/skills.yaml",
        """
python_skill:
  path: ai/skills/python/example.md
  description: Python guidance
saas_auth:
  path: ai/skills/saas/auth.md
  description: SaaS guidance
""",
    )
    _write(project_root / "ai/skills/python/example.md", "# Python\n")
    _write(project_root / "ai/skills/saas/auth.md", "# SaaS\n")
    _write(project_root / "src/main.py", "import json\n")
    _write(
        project_root / ".template-profile.yaml",
        f"""
schema_version: 1
environment: local
capabilities:
  languages:
    python:
      enabled: true
  frameworks:
    react:
      enabled: false
  business:
    saas:
      enabled: {str(enable_saas).lower()}
dependency_policy:
  include_dev: true
  additional_extras: []
  additional_groups: []
""",
    )


def test_validate_consistency_checks_active_skill_files(tmp_path: Path) -> None:
    _create_sample_project(tmp_path, enable_saas=False)

    assert validate_consistency(tmp_path) == {"missing": [], "gated": []}

    (tmp_path / "ai/skills/python/example.md").unlink()
    assert validate_consistency(tmp_path)["missing"] == ["ai/skills/python/example.md"]


def test_restore_dry_run_reports_explicit_implicit_and_disabled(
    tmp_path: Path,
) -> None:
    _create_sample_project(tmp_path)

    payload = restore_project(tmp_path, dry_run=True)

    assert payload["explicit_capabilities"] == [
        "languages:python",
        "business:saas",
    ]
    assert payload["implicit_capabilities"] == ["frameworks:react"]
    assert payload["disabled_capabilities"] == []
    assert payload["dependencies"]["status"] == "skipped"
    assert payload["context"]["status"] == "skipped"


def test_restore_regenerates_filtered_context_artifacts(tmp_path: Path) -> None:
    _create_sample_project(tmp_path, enable_saas=False)

    payload = restore_project(tmp_path, dry_run=False)

    assert payload["context"]["status"] == "ok"
    registry = (tmp_path / ".ai/skills_registry.json").read_text(encoding="utf-8")
    assert "python_skill" in registry
    assert "saas_auth" not in registry
    assert (tmp_path / "llms.txt").exists()


def test_enabling_capability_changes_generated_skill_registry(tmp_path: Path) -> None:
    _create_sample_project(tmp_path, enable_saas=False)
    restore_project(tmp_path, dry_run=False)
    disabled_registry = (tmp_path / ".ai/skills_registry.json").read_text(
        encoding="utf-8"
    )

    profile_path = tmp_path / ".template-profile.yaml"
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8").replace(
            "saas:\n      enabled: false", "saas:\n      enabled: true"
        ),
        encoding="utf-8",
    )
    restore_project(tmp_path, dry_run=False)
    enabled_registry = (tmp_path / ".ai/skills_registry.json").read_text(
        encoding="utf-8"
    )

    assert "saas_auth" not in disabled_registry
    assert "saas_auth" in enabled_registry


def test_restore_is_idempotent(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    first = restore_project(tmp_path, dry_run=False)

    def normalized(relative: str) -> str:
        content = (tmp_path / relative).read_text(encoding="utf-8")
        if relative.endswith("dependencies_graph.json"):
            payload = json.loads(content)
            payload.pop("generated_at", None)
            return json.dumps(payload, sort_keys=True)
        return content

    snapshot = {
        relative: normalized(relative) for relative in first["context"]["artifacts"]
    }
    second = restore_project(tmp_path, dry_run=False)

    assert second["context"]["artifacts"] == first["context"]["artifacts"]
    assert {
        relative: normalized(relative) for relative in second["context"]["artifacts"]
    } == snapshot
