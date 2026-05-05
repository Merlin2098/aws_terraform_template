from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ai.installer import install_template


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_local_install_copies_only_local_and_dev_requirements(tmp_path: Path) -> None:
    target = tmp_path / "host-local"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert "requirements.local.txt" in summary["copied"]
    assert "requirements.dev.txt" in summary["copied"]
    assert "requirements.cloud.txt" not in summary["copied"]
    assert "pyproject.toml" not in summary["copied"]
    assert "uv.lock" not in summary["copied"]
    assert not (target / "requirements.txt").exists()
    assert (target / "requirements.local.txt").exists()
    assert (target / "requirements.dev.txt").exists()
    assert not (target / "requirements.cloud.txt").exists()
    assert not (target / "pyproject.toml").exists()
    assert not (target / "uv.lock").exists()
    assert summary["gitignore_updates"] == []
    gitignore = (target / ".gitignore").read_text(encoding="utf-8")
    assert ".ai/" in gitignore
    assert ".venv/" in gitignore
    assert "Makefile" not in gitignore


def test_cloud_install_copies_cloud_requirements(tmp_path: Path) -> None:
    target = tmp_path / "host-cloud"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="cloud",
        package_manager="pip",
    )

    assert "requirements.local.txt" in summary["copied"]
    assert "requirements.dev.txt" in summary["copied"]
    assert "requirements.cloud.txt" in summary["copied"]
    assert "pyproject.toml" not in summary["copied"]
    assert "uv.lock" not in summary["copied"]
    assert not (target / "requirements.txt").exists()
    assert (target / "requirements.cloud.txt").exists()

    pre_commit = (target / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    makefile = (target / "Makefile").read_text(encoding="utf-8")
    assert "args: [--manager, pip, --profile, cloud]" in pre_commit
    assert "$(BOOTSTRAP_PYTHON) scripts/run_pip_init.py --profile cloud" in makefile


def test_existing_host_requirements_txt_is_left_untouched(tmp_path: Path) -> None:
    target = tmp_path / "host-existing"
    target.mkdir(parents=True)
    requirements_txt = target / "requirements.txt"
    original = "custom-package==1.0.0\n"
    requirements_txt.write_text(original, encoding="utf-8")

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert requirements_txt.read_text(encoding="utf-8") == original


def test_existing_host_gitignore_gets_only_missing_template_entries(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-existing-gitignore"
    target.mkdir(parents=True)
    host_gitignore = target / ".gitignore"
    host_gitignore.write_text("logs/\ncustom.tmp\n.ai/\n", encoding="utf-8")

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert ".gitignore" in summary["skipped"]
    assert ".venv/" in summary["gitignore_updates"]
    assert ".ai/" not in summary["gitignore_updates"]
    assert "Makefile" not in summary["gitignore_updates"]

    gitignore = host_gitignore.read_text(encoding="utf-8")
    assert "custom.tmp" in gitignore
    assert gitignore.count(".ai/") == 1
    assert ".venv/" in gitignore
    assert "Makefile" not in gitignore


def test_uv_local_install_copies_only_uv_project_files(tmp_path: Path) -> None:
    target = tmp_path / "host-uv-local"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="uv",
    )

    assert "pyproject.toml" in summary["copied"]
    assert "uv.lock" in summary["copied"]
    assert "requirements.local.txt" not in summary["copied"]
    assert "requirements.dev.txt" not in summary["copied"]
    assert "requirements.cloud.txt" not in summary["copied"]
    assert (target / "pyproject.toml").exists()
    assert (target / "uv.lock").exists()
    assert not (target / "requirements.local.txt").exists()
    assert not (target / "requirements.dev.txt").exists()
    assert not (target / "requirements.cloud.txt").exists()


def test_uv_cloud_install_renders_local_hook_and_makefile(tmp_path: Path) -> None:
    target = tmp_path / "host-uv-cloud"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="cloud",
        package_manager="uv",
    )

    pre_commit = (target / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    makefile = (target / "Makefile").read_text(encoding="utf-8")

    assert "args: [--manager, uv, --profile, local]" in pre_commit
    assert "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init" in makefile
    assert "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py update" in makefile
    assert "uv run python scripts/package.py --package-manager uv" in makefile


def test_include_structure_creates_empty_tests_dir_without_template_tests(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-with-structure"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=True,
        environment_profile="local",
        package_manager="pip",
    )

    tests_dir = target / "tests"
    assert tests_dir.exists()
    assert tests_dir.is_dir()
    assert list(tests_dir.iterdir()) == []
    assert "tests" in summary["created_dirs"]
    assert "tests/test_installer.py" in summary["ignored"]


def test_without_structure_does_not_create_tests_dir(tmp_path: Path) -> None:
    target = tmp_path / "host-without-structure"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert not (target / "tests").exists()


def test_installer_rejects_conflicting_package_manager_flags(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "install_linux.py",
            "--target",
            str(tmp_path / "host"),
            "--without-structure",
            "--local",
            "--pip",
            "--uv",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "mutually exclusive" in result.stderr
