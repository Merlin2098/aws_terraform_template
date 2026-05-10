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
    assert not (target / ".template-profile").exists()
    # The 3 host-extra entries (ai/, data/, /prompt/) are not in the copied
    # .gitignore, so append_target_gitignore adds them as updates.
    assert set(summary["gitignore_updates"]) == {"ai/", "data/", "/prompt/"}
    gitignore = (target / ".gitignore").read_text(encoding="utf-8")
    assert ".ai/" in gitignore
    assert ".venv/" in gitignore
    assert "ai/" in gitignore
    assert "data/" in gitignore
    assert "/prompt/" in gitignore
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
    assert "ai/" in summary["gitignore_updates"]
    assert "data/" in summary["gitignore_updates"]
    assert "/prompt/" in summary["gitignore_updates"]
    assert "Makefile" not in summary["gitignore_updates"]

    gitignore = host_gitignore.read_text(encoding="utf-8")
    assert "custom.tmp" in gitignore
    assert gitignore.count(".ai/") == 1
    assert ".venv/" in gitignore
    assert "ai/" in gitignore
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
    assert ".template-profile" in summary["copied"]
    assert "requirements.local.txt" not in summary["copied"]
    assert "requirements.dev.txt" not in summary["copied"]
    assert "requirements.cloud.txt" not in summary["copied"]
    assert (target / "pyproject.toml").exists()
    assert (target / "uv.lock").exists()
    assert (target / ".template-profile").read_text(encoding="utf-8") == (
        "package_manager=uv\nenvironment_profile=local\n"
    )
    assert not (target / "requirements.local.txt").exists()
    assert not (target / "requirements.dev.txt").exists()
    assert not (target / "requirements.cloud.txt").exists()


def test_uv_cloud_install_renders_cloud_profile_defaults(tmp_path: Path) -> None:
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
    template_profile = (target / ".template-profile").read_text(encoding="utf-8")

    assert "args: [--manager, uv]" in pre_commit
    assert "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init" in makefile
    assert "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py update" in makefile
    assert "uv run python scripts/package.py --package-manager uv" in makefile
    assert template_profile == "package_manager=uv\nenvironment_profile=cloud\n"


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


def test_settings_local_json_is_not_copied_to_host(tmp_path: Path) -> None:
    target = tmp_path / "host-settings"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert ".claude/settings.local.json" not in summary["copied"]
    assert any(
        p == ".claude/settings.local.json" or p.endswith("settings.local.json")
        for p in summary["ignored"]
    )
    assert ".claude/settings.json" in summary["copied"]
    assert (target / ".claude" / "settings.json").exists()
    assert not (target / ".claude" / "settings.local.json").exists()


def test_docs_directory_is_copied_to_host(tmp_path: Path) -> None:
    target = tmp_path / "host-docs"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert "docs/terra_principles.md" in summary["copied"]
    # README.md is excluded by name in is_excluded(); check a different file.
    assert "docs/windows_setup/make_cheatlist.md" in summary["copied"]
    assert (target / "docs" / "terra_principles.md").exists()
    assert (target / "docs" / "windows_setup" / "make_cheatlist.md").exists()


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
