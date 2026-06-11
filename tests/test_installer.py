from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ai.installer import (
    gated_paths_to_exclude,
    install_template,
    should_copy_capability_path,
    validate_capability_profile,
)
from ai.runtime.capability_registry import load_registry


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
    # Host-extra entries are not in the copied .gitignore, so
    # append_target_gitignore adds them as updates.
    assert {
        "ai/",
        "docs/linux_setup/",
        "docs/windows_setup/",
        "specs/template/",
        "specs/README.md",
        "docs/terra_principles.md",
        "docs/terraform_cheatsheet.md",
        "docs/treemap.md",
        "data/",
        "/prompt/",
        ".claude/settings.local.json",
    }.issubset(set(summary["gitignore_updates"]))
    gitignore = (target / ".gitignore").read_text(encoding="utf-8")
    assert ".ai/" in gitignore
    assert ".venv/" in gitignore
    assert "ai/" in gitignore
    assert "data/" in gitignore
    assert "/prompt/" in gitignore
    assert ".claude/settings.local.json" in gitignore
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
    assert "docs/linux_setup/" in summary["gitignore_updates"]
    assert "data/" in summary["gitignore_updates"]
    assert "/prompt/" in summary["gitignore_updates"]
    assert ".claude/settings.local.json" in summary["gitignore_updates"]
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
        "package_manager=uv\nenvironment_profile=local\ncapability_profile=\n"
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
    assert template_profile == (
        "package_manager=uv\nenvironment_profile=cloud\ncapability_profile=\n"
    )


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
    assert "docs/linux_setup/make_cheatlist.md" in summary["copied"]
    assert (target / "docs" / "terra_principles.md").exists()
    assert (target / "docs" / "windows_setup" / "make_cheatlist.md").exists()
    assert (target / "docs" / "linux_setup" / "make_cheatlist.md").exists()


def test_linux_setup_readme_stays_template_only(tmp_path: Path) -> None:
    target = tmp_path / "host-linux-docs"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert "docs/linux_setup/README.md" not in summary["copied"]
    assert "docs/linux_setup/README.md" in summary["ignored"]
    assert not (target / "docs" / "linux_setup" / "README.md").exists()


def test_validate_capability_profile_accepts_registry_names() -> None:
    registry = load_registry(REPO_ROOT)

    assert validate_capability_profile("saas", registry) == "saas"
    assert validate_capability_profile(None, registry) is None
    assert validate_capability_profile("", registry) is None


def test_validate_capability_profile_rejects_unknown_name() -> None:
    registry = load_registry(REPO_ROOT)

    with pytest.raises(ValueError, match="saas"):
        validate_capability_profile("not-a-capability", registry)


def test_gated_paths_to_exclude_excludes_unselected_business_capability() -> None:
    registry = load_registry(REPO_ROOT)

    excluded = gated_paths_to_exclude(registry, {})

    assert "ai/skills/saas/" in excluded
    assert "ai/domains/saas.md" in excluded
    assert "requirements.saas.txt" in excluded


def test_gated_paths_to_exclude_keeps_selected_business_capability() -> None:
    registry = load_registry(REPO_ROOT)

    excluded = gated_paths_to_exclude(registry, {"business": ["saas"]})

    assert excluded == set()


def test_should_copy_capability_path_matches_excluded_prefixes() -> None:
    excluded = {"ai/skills/saas/", "ai/domains/saas.md"}

    assert not should_copy_capability_path(Path("ai/skills/saas/auth.md"), excluded)
    assert not should_copy_capability_path(Path("ai/domains/saas.md"), excluded)
    assert should_copy_capability_path(Path("ai/domains/aws.md"), excluded)


def test_install_without_capability_excludes_saas_paths(tmp_path: Path) -> None:
    target = tmp_path / "host-no-saas"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
    )

    assert "ai/domains/saas.md" not in summary["copied"]
    assert "ai/skills/saas/auth.md" not in summary["copied"]
    assert "requirements.saas.txt" not in summary["copied"]
    assert "ai/domains/saas.md" in summary["ignored"]
    assert not (target / "ai" / "domains" / "saas.md").exists()
    assert not (target / "requirements.saas.txt").exists()


def test_install_with_saas_capability_includes_saas_paths(tmp_path: Path) -> None:
    target = tmp_path / "host-saas"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
        package_manager="pip",
        capability_profile="saas",
    )

    assert "ai/domains/saas.md" in summary["copied"]
    assert "ai/skills/saas/auth.md" in summary["copied"]
    assert "requirements.saas.txt" in summary["copied"]
    assert (target / "ai" / "domains" / "saas.md").exists()
    assert (target / "requirements.saas.txt").exists()


def test_install_with_saas_capability_writes_typed_capabilities_block(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-uv-saas"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="cloud",
        package_manager="uv",
        capability_profile="saas",
    )

    template_profile = (target / ".template-profile").read_text(encoding="utf-8")

    assert template_profile.startswith(
        "package_manager=uv\nenvironment_profile=cloud\ncapability_profile=saas\n"
    )
    assert "capabilities:" in template_profile
    assert "business:" in template_profile
    assert "- saas" in template_profile


def test_install_without_capability_omits_typed_capabilities_block(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-uv-no-saas"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="cloud",
        package_manager="uv",
    )

    template_profile = (target / ".template-profile").read_text(encoding="utf-8")

    assert template_profile == (
        "package_manager=uv\nenvironment_profile=cloud\ncapability_profile=\n"
    )
    assert "capabilities:" not in template_profile


def test_run_uv_sync_uses_template_profile_and_can_skip_dev_groups(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.run_uv_sync as run_uv_sync

    profile_file = tmp_path / ".template-profile"
    profile_file.write_text("environment_profile=cloud\n", encoding="utf-8")

    monkeypatch.setattr(run_uv_sync, "PROFILE_FILE", profile_file)
    monkeypatch.setattr(run_uv_sync.shutil, "which", lambda name: None)

    assert run_uv_sync.resolve_profile(None) == "cloud"
    command = run_uv_sync.sync_command(
        "local", use_dev_dependencies=False, python_path="/usr/bin/python3"
    )
    assert command == [
        "/usr/bin/python3",
        "-m",
        "uv",
        "sync",
        "--no-dev",
    ]

    cloud_command = run_uv_sync.sync_command(
        "cloud", use_dev_dependencies=False, python_path="/usr/bin/python3"
    )
    assert cloud_command == [
        "/usr/bin/python3",
        "-m",
        "uv",
        "sync",
        "--extra",
        "local",
        "--extra",
        "cloud",
        "--no-dev",
    ]


def test_run_uv_sync_parse_args_rejects_conflicting_dev_flags(monkeypatch) -> None:
    import pytest
    import scripts.run_uv_sync as run_uv_sync

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_uv_sync.py", "init", "--include-dev", "--no-dev"],
    )

    with pytest.raises(SystemExit):
        run_uv_sync.parse_args()


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
