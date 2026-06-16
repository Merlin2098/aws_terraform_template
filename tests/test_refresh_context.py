from __future__ import annotations

from pathlib import Path

from ai.runtime.config import artifact_paths, load_context_config
from ai.tools.refresh_context import refresh_context


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_sample_project(project_root: Path) -> None:
    artifacts = """artifacts:
  - .ai/context_bundle.yaml
  - .ai/skills_registry.json
  - .ai/dependencies_graph.json
  - .ai/treemap.md
"""

    _write(
        project_root / "ai" / "context.yaml",
        artifacts
        + """
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
        project_root / "ai" / "skills.yaml",
        """example_skill:
  path: ai/skills/python/example.md
  description: Example skill
""",
    )
    _write(project_root / "ai" / "skills" / "python" / "example.md", "# Example\n")
    _write(project_root / "src" / "jobs" / "example_job.py", "import json\n")
    _write(project_root / "scripts" / "helper.py", "print('ok')\n")


def test_refresh_context_always_writes_full_artifact_set(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    payload = refresh_context(tmp_path)

    expected = {
        ".ai/context_bundle.yaml",
        ".ai/skills_registry.json",
        ".ai/dependencies_graph.json",
        ".ai/treemap.md",
    }
    assert payload["status"] == "ok"
    assert payload["mode"] == "full"
    assert set(payload["artifacts"]) == expected

    for relative_path in expected:
        assert (tmp_path / relative_path).exists()


def test_artifact_paths_reads_simplified_context_config(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    config = load_context_config(tmp_path)

    assert artifact_paths(config) == [
        ".ai/context_bundle.yaml",
        ".ai/skills_registry.json",
        ".ai/dependencies_graph.json",
        ".ai/treemap.md",
    ]
