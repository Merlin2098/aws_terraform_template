from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from ai.installer import (
    STATE_FILENAME,
    framework_version,
    install_template,
    is_framework_owned,
    read_state,
    update_template,
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


def test_docs_directory_is_not_copied_to_host(tmp_path: Path) -> None:
    target = tmp_path / "host-docs"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    assert not any(p.startswith("docs/") or p == "docs" for p in summary["copied"])
    assert "docs" in summary["ignored"]
    assert not (target / "docs").exists()


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


# --- versioning & update_template tests ---


def test_framework_version_returns_semver_string() -> None:
    version = framework_version()
    parts = version.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_is_framework_owned_classifies_correctly() -> None:
    assert is_framework_owned(Path("AGENTS.md")) is True
    assert is_framework_owned(Path("ai/skills/terraform/terraform_style.md")) is True
    assert is_framework_owned(Path("scripts/run_uv_sync.py")) is True
    assert is_framework_owned(Path("src/jobs/my_job.py")) is False
    assert is_framework_owned(Path("infra/main.tf")) is False
    assert is_framework_owned(Path("tests/test_something.py")) is False
    assert is_framework_owned(Path(".template-profile.yaml")) is False
    assert is_framework_owned(Path("specs/project/my_spec.md")) is False


def test_install_writes_framework_state(tmp_path: Path) -> None:
    target = tmp_path / "host-state"

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    state_file = target / STATE_FILENAME
    assert state_file.exists(), f"{STATE_FILENAME} not written after install"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["framework_version"] == framework_version()
    assert state["include_structure"] is False
    assert isinstance(state["framework_manifest"], list)
    assert len(state["framework_manifest"]) > 0
    assert "AGENTS.md" in state["framework_manifest"]
    assert ".template-profile.yaml" not in state["framework_manifest"]


def test_install_dry_run_does_not_write_state(tmp_path: Path) -> None:
    target = tmp_path / "host-dry"

    install_template(
        target=target,
        force=False,
        dry_run=True,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    assert not (target / STATE_FILENAME).exists()


def test_update_overwrites_framework_owned_file(tmp_path: Path) -> None:
    target = tmp_path / "host-update"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    agents_md = target / "AGENTS.md"
    original = agents_md.read_text(encoding="utf-8")
    agents_md.write_text("# TAMPERED\n", encoding="utf-8")

    # Force update even when version matches
    update_template(target=target, force=True, dry_run=False)

    assert agents_md.read_text(encoding="utf-8") == original


def test_update_leaves_host_owned_file_untouched(tmp_path: Path) -> None:
    target = tmp_path / "host-host-owned"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=True,
        enabled_capabilities=["none"],
    )

    host_file = target / "src" / "custom_job.py"
    host_file.parent.mkdir(parents=True, exist_ok=True)
    host_file.write_text("# custom\n", encoding="utf-8")

    update_template(target=target, force=True, dry_run=False)

    assert host_file.read_text(encoding="utf-8") == "# custom\n"


def test_update_deletes_orphaned_framework_file(tmp_path: Path) -> None:
    target = tmp_path / "host-orphan"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    # Plant a fake orphan: write the file and inject it into the saved manifest
    orphan_path = target / "ai" / "skills" / "obsolete_skill.md"
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_text("# old skill\n", encoding="utf-8")

    state_file = target / STATE_FILENAME
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["framework_manifest"].append("ai/skills/obsolete_skill.md")
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    summary = update_template(target=target, force=True, dry_run=False)

    assert "ai/skills/obsolete_skill.md" in summary["deleted"]
    assert not orphan_path.exists()


def test_update_without_state_raises_value_error(tmp_path: Path) -> None:
    target = tmp_path / "host-no-state"
    target.mkdir()

    with pytest.raises(ValueError, match="No framework state found"):
        update_template(target=target)


def test_update_idempotent_when_version_matches(tmp_path: Path) -> None:
    target = tmp_path / "host-idempotent"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    summary = update_template(target=target, force=False, dry_run=False)

    assert summary["up_to_date"] is True
    assert summary["copied"] == []
    assert summary["deleted"] == []


def test_update_dry_run_does_not_modify_files(tmp_path: Path) -> None:
    target = tmp_path / "host-dry-update"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    agents_md = target / "AGENTS.md"
    agents_md.write_text("# TAMPERED\n", encoding="utf-8")

    update_template(target=target, force=True, dry_run=True)

    assert agents_md.read_text(encoding="utf-8") == "# TAMPERED\n"
