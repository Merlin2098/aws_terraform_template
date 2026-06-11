from __future__ import annotations

from pathlib import Path

from ai.runtime.llms_txt import build_and_persist_llms_txt, build_llms_txt


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_sample_project(project_root: Path) -> None:
    _write(
        project_root / "ai" / "context.yaml",
        """artifacts:
  - .ai/context_bundle.yaml
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

rules: []

entrypoint_roots:
  directories:
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


def test_build_llms_txt_includes_project_summary_and_skills(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    content = build_llms_txt(tmp_path)

    assert content.startswith("# Project AI Guide")
    assert tmp_path.name not in content
    assert "Do not infer behavior from the repository name." in content
    assert "## Architecture" in content
    assert "## Capabilities" in content
    assert "## Skills / Guidance" in content
    assert "ai/skills/python/example.md: Example skill" in content
    assert "## Relevant Specs" in content
    assert "(no specs/ directory" in content
    assert "## Agent Onboarding" in content


def test_build_llms_txt_lists_active_capabilities(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)
    _write(
        tmp_path / "ai" / "capabilities" / "languages" / "python.yaml",
        "name: python\ntype: language\n",
    )
    _write(
        tmp_path / ".template-profile.yaml",
        "schema_version: 1\n"
        "environment: local\n"
        "capabilities:\n"
        "  languages:\n"
        "    python:\n"
        "      enabled: true\n"
        "dependency_policy: {}\n",
    )

    content = build_llms_txt(tmp_path)

    assert "- python (languages/language)" in content


def test_build_llms_txt_lists_specs_when_present(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)
    _write(tmp_path / "specs" / "template" / "001-contract.md", "# Contract\n")
    _write(tmp_path / "specs" / "project" / "README.md", "# Project specs\n")

    content = build_llms_txt(tmp_path)

    assert "specs/template/001-contract.md" in content
    assert "specs/project/README.md" in content


def test_build_and_persist_llms_txt_writes_file(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    output_path = tmp_path / "llms.txt"
    content = build_and_persist_llms_txt(tmp_path, output_path)

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == content
