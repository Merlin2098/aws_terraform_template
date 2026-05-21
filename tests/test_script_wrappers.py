from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_ai_refresh_wrapper_smoke(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/hooks/ai_refresh.py",
            "--project-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"mode": "full"' in result.stdout


def test_ruff_wrappers_smoke() -> None:
    check_result = subprocess.run(
        [
            sys.executable,
            "scripts/testing/run_ruff_check.py",
            "tests/test_example_job.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    format_result = subprocess.run(
        [
            sys.executable,
            "scripts/testing/run_ruff_format.py",
            "--check",
            "tests/test_example_job.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert check_result.returncode == 0, check_result.stderr
    assert format_result.returncode == 0, format_result.stderr


def test_pytest_wrapper_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/testing/run_pytest.py", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "pytest" in result.stdout.lower()


def test_pytest_wrapper_treats_no_tests_as_success(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "[project]\nname = 'empty-tests'\nversion = '0.0.0'\n",
    )

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/testing/run_pytest.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "No tests were collected" in result.stdout


def test_pip_init_wrapper_dry_run() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_pip_init.py", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "pip install -r requirements.local.txt -r requirements.dev.txt" in result.stdout


def test_uv_sync_wrapper_dry_run_init() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_uv_sync.py", "init", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "sync --group dev-local" in result.stdout


def test_uv_sync_wrapper_reads_persisted_cloud_profile(tmp_path: Path) -> None:
    profile_path = REPO_ROOT / ".template-profile"
    original = profile_path.read_text(encoding="utf-8")
    try:
        profile_path.write_text(
            "package_manager=uv\nenvironment_profile=cloud\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, "scripts/run_uv_sync.py", "init", "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        profile_path.write_text(original, encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert "sync --extra local --extra cloud --group dev-local --group dev-cloud" in result.stdout
