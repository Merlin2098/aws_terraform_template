from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

from ai.installer import (
    install_template,
    validate_enabled_capabilities,
)
from ai.runtime.capability_registry import load_registry
from ai.runtime.project_profile import resolve_project_profile


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_existing_host_file_is_left_untouched(tmp_path: Path) -> None:
    target = tmp_path / "host-existing"
    target.mkdir(parents=True)
    custom_file = target / "pyproject.toml"
    original = "[project]\nname = 'custom'\n"
    custom_file.write_text(original, encoding="utf-8")

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    assert custom_file.read_text(encoding="utf-8") == original


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
        enabled_capabilities=["none"],
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


def test_install_without_selection_enables_full_catalog(tmp_path: Path) -> None:
    target = tmp_path / "host-all-capabilities"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
    )

    assert "pyproject.toml" in summary["copied"]
    assert "uv.lock" in summary["copied"]
    assert ".template-profile.yaml" in summary["copied"]
    assert (target / "pyproject.toml").exists()
    assert (target / "uv.lock").exists()
    profile = yaml.safe_load(
        (target / ".template-profile.yaml").read_text(encoding="utf-8")
    )
    assert profile["capabilities"]["languages"]["python"]["enabled"] is True
    assert profile["capabilities"]["cloud"]["aws"]["enabled"] is True
    assert profile["capabilities"]["business"]["saas"]["enabled"] is True
    resolved = resolve_project_profile(target)
    assert resolved.disabled_capabilities == ()
    assert set(resolved.explicit_capabilities) == set(
        validate_enabled_capabilities([], load_registry(REPO_ROOT))
    )


def test_none_selection_disables_full_catalog(tmp_path: Path) -> None:
    target = tmp_path / "host-no-capabilities"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    makefile = (target / "Makefile").read_text(encoding="utf-8")
    template_profile = yaml.safe_load(
        (target / ".template-profile.yaml").read_text(encoding="utf-8")
    )

    assert "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py init" in makefile
    assert "$(BOOTSTRAP_PYTHON) scripts/run_uv_sync.py update" in makefile
    assert "environment" not in template_profile
    assert template_profile["capabilities"]["languages"]["python"]["enabled"] is False
    assert template_profile["capabilities"]["cloud"]["aws"]["enabled"] is False


def test_include_structure_creates_empty_tests_dir_without_template_tests(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-with-structure"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=True,
        enabled_capabilities=["none"],
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
        enabled_capabilities=["none"],
    )

    assert not (target / "tests").exists()


def test_settings_local_json_is_not_copied_to_host(tmp_path: Path) -> None:
    target = tmp_path / "host-settings"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
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
        enabled_capabilities=["none"],
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
        enabled_capabilities=["none"],
    )

    assert "docs/linux_setup/README.md" not in summary["copied"]
    assert "docs/linux_setup/README.md" in summary["ignored"]
    assert not (target / "docs" / "linux_setup" / "README.md").exists()


def test_install_with_none_keeps_full_catalog_files(tmp_path: Path) -> None:
    target = tmp_path / "host-no-saas"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    assert "ai/domains/saas.md" in summary["copied"]
    assert "ai/skills/saas/auth.md" in summary["copied"]
    assert (target / "ai" / "domains" / "saas.md").exists()


def test_install_with_saas_capability_includes_saas_paths(tmp_path: Path) -> None:
    target = tmp_path / "host-saas"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["business:saas"],
    )

    assert "ai/domains/saas.md" in summary["copied"]
    assert "ai/skills/saas/auth.md" in summary["copied"]
    assert (target / "ai" / "domains" / "saas.md").exists()


def test_install_with_saas_capability_writes_typed_capabilities_block(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-uv-saas"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["business:saas"],
    )

    template_profile = yaml.safe_load(
        (target / ".template-profile.yaml").read_text(encoding="utf-8")
    )

    assert "environment" not in template_profile
    assert template_profile["capabilities"]["business"]["saas"]["enabled"] is True
    assert (
        template_profile["capabilities"]["infrastructure"]["terraform"]["enabled"]
        is False
    )


def test_install_with_none_writes_disabled_catalog_entries(
    tmp_path: Path,
) -> None:
    target = tmp_path / "host-uv-no-saas"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    template_profile = yaml.safe_load(
        (target / ".template-profile.yaml").read_text(encoding="utf-8")
    )

    assert template_profile["capabilities"]["business"]["saas"]["enabled"] is False
    assert template_profile["capabilities"]["databases"]["supabase"]["enabled"] is False


def test_validate_enabled_capabilities_accepts_multiple_categories() -> None:
    registry = load_registry(REPO_ROOT)

    assert validate_enabled_capabilities(["cloud:aws", "business:saas"], registry) == [
        "cloud:aws",
        "business:saas",
    ]


def test_validate_enabled_capabilities_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unknown capability"):
        validate_enabled_capabilities(["cloud:azure"])


def test_validate_enabled_capabilities_defaults_to_all() -> None:
    registry = load_registry(REPO_ROOT)

    assert validate_enabled_capabilities([], registry) == [
        f"{category}:{name}"
        for category in sorted(registry)
        for name in sorted(registry[category])
    ]


def test_validate_enabled_capabilities_accepts_none() -> None:
    assert validate_enabled_capabilities(["none"]) == []


def test_validate_enabled_capabilities_rejects_none_with_other_values() -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        validate_enabled_capabilities(["none", "languages:python"])


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
