from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from ai.installer import (
    STATE_FILENAME,
    _classify,
    _manifest_as_map,
    compute_tree_digest,
    file_sha256,
    framework_version,
    install_template,
    is_framework_owned,
    read_state,
    text_sha256,
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
    # uv.lock and Makefile are host-owned — never distributed by the framework.
    assert "uv.lock" not in summary["copied"]
    assert "Makefile" not in summary["copied"]
    assert not (target / "uv.lock").exists()
    assert not (target / "Makefile").exists()
    assert ".template-profile.yaml" in summary["copied"]
    assert (target / "pyproject.toml").exists()
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

    # Makefile is host-owned and no longer distributed by the framework.
    assert not (target / "Makefile").exists()
    template_profile = yaml.safe_load(
        (target / ".template-profile.yaml").read_text(encoding="utf-8")
    )

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
    # .claude/settings.json is host-owned — no longer distributed by the framework.
    assert ".claude/settings.json" not in summary["copied"]
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
    # manifest is now a dict {path: {sha256, ownership}} — ADR-FW-003
    manifest = state["framework_manifest"]
    assert isinstance(manifest, dict)
    assert len(manifest) > 0
    assert "AGENTS.md" in manifest
    assert manifest["AGENTS.md"]["ownership"] == "managed"
    assert isinstance(manifest["AGENTS.md"]["sha256"], str)
    assert len(manifest["AGENTS.md"]["sha256"]) == 64  # sha256 hex
    assert ".template-profile.yaml" not in manifest
    # tree_digest must be present and stable
    assert isinstance(state.get("tree_digest"), str)
    assert len(state["tree_digest"]) == 64


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
    # manifest is now a dict — add the orphan entry
    manifest = state["framework_manifest"]
    if isinstance(manifest, list):
        manifest.append("ai/skills/obsolete_skill.md")
    else:
        manifest["ai/skills/obsolete_skill.md"] = {
            "sha256": "deadbeef",
            "ownership": "managed",
        }
    state["framework_manifest"] = manifest
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    summary = update_template(target=target, force=True, dry_run=False)

    assert "ai/skills/obsolete_skill.md" in summary["deleted"]
    assert not orphan_path.exists()


def test_update_without_state_raises_value_error(tmp_path: Path) -> None:
    target = tmp_path / "host-no-state"
    target.mkdir()

    with pytest.raises(ValueError, match="No framework state found"):
        update_template(target=target)


def test_update_idempotent_when_tree_digest_matches(tmp_path: Path) -> None:
    target = tmp_path / "host-idempotent"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    summary = update_template(target=target, force=False, dry_run=False)

    # up_to_date is driven by tree_digest, not version string (ADR-FW-003)
    assert summary["up_to_date"] is True
    assert summary["updated"] == []
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


# --- ADR-FW-003: content fingerprint tests ---


def test_file_sha256_normalises_crlf(tmp_path: Path) -> None:
    lf = tmp_path / "lf.txt"
    crlf = tmp_path / "crlf.txt"
    lf.write_bytes(b"hello\nworld\n")
    crlf.write_bytes(b"hello\r\nworld\r\n")
    assert file_sha256(lf) == file_sha256(crlf)


def test_text_sha256_matches_file_sha256(tmp_path: Path) -> None:
    content = "hello\nworld\n"
    path = tmp_path / "file.txt"
    path.write_text(content, encoding="utf-8")
    assert text_sha256(content) == file_sha256(path)


def test_compute_tree_digest_stable_across_calls(tmp_path: Path) -> None:
    manifest = {
        "AGENTS.md": {"sha256": "abc123", "ownership": "managed"},
        "ai/skills/foo.md": {"sha256": "def456", "ownership": "managed"},
    }
    assert compute_tree_digest(manifest) == compute_tree_digest(manifest)


def test_compute_tree_digest_changes_when_manifest_changes() -> None:
    manifest_a = {"AGENTS.md": {"sha256": "aaa", "ownership": "managed"}}
    manifest_b = {"AGENTS.md": {"sha256": "bbb", "ownership": "managed"}}
    assert compute_tree_digest(manifest_a) != compute_tree_digest(manifest_b)


def test_install_writes_manifest_map_with_sha256_and_ownership(tmp_path: Path) -> None:
    target = tmp_path / "host-manifest-map"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    state = json.loads((target / STATE_FILENAME).read_text(encoding="utf-8"))
    manifest = state["framework_manifest"]
    assert isinstance(manifest, dict)
    for path, entry in manifest.items():
        assert "sha256" in entry, f"{path} missing sha256"
        assert "ownership" in entry, f"{path} missing ownership"
        assert entry["ownership"] in ("managed", "generated", "append-only")
        assert isinstance(entry["sha256"], str) and len(entry["sha256"]) == 64


def test_install_writes_tree_digest(tmp_path: Path) -> None:
    target = tmp_path / "host-tree-digest"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    state = json.loads((target / STATE_FILENAME).read_text(encoding="utf-8"))
    assert "tree_digest" in state
    assert len(state["tree_digest"]) == 64

    # Second install to same target (force) produces the same tree_digest.
    install_template(
        target=target,
        force=True,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    state2 = json.loads((target / STATE_FILENAME).read_text(encoding="utf-8"))
    assert state["tree_digest"] == state2["tree_digest"]


def test_update_short_circuits_when_tree_digest_unchanged(tmp_path: Path) -> None:
    target = tmp_path / "host-short-circuit"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    # Even if we set a different framework_version label, tree_digest drives up_to_date.
    state_file = target / STATE_FILENAME
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["framework_version"] = "0.0.0-old"
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    summary = update_template(target=target, force=False, dry_run=False)
    assert summary["up_to_date"] is True


def test_update_detects_locally_modified_file(tmp_path: Path) -> None:
    target = tmp_path / "host-local-mod"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    # Host edits a framework-owned file.
    agents_md = target / "AGENTS.md"
    original = agents_md.read_text(encoding="utf-8")
    agents_md.write_text("# HOST EDITED\n", encoding="utf-8")

    summary = update_template(target=target, force=False, dry_run=False)

    assert "AGENTS.md" in summary["locally_modified"]
    # File must be preserved (not overwritten).
    assert agents_md.read_text(encoding="utf-8") == "# HOST EDITED\n"
    assert "AGENTS.md" not in summary.get("updated", [])


def test_update_force_overwrites_locally_modified_file(tmp_path: Path) -> None:
    target = tmp_path / "host-force-overwrite"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    agents_md = target / "AGENTS.md"
    original = agents_md.read_text(encoding="utf-8")
    agents_md.write_text("# HOST EDITED\n", encoding="utf-8")

    update_template(target=target, force=True, dry_run=False)

    assert agents_md.read_text(encoding="utf-8") == original


def test_update_detects_conflict_when_both_sides_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "host-conflict"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    # Simulate host editing AGENTS.md.
    agents_md = target / "AGENTS.md"
    agents_md.write_text("# HOST EDITED\n", encoding="utf-8")

    # Simulate template changing AGENTS.md by patching its sha256 in the state.
    state_file = target / STATE_FILENAME
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["framework_manifest"]["AGENTS.md"]["sha256"] = "0" * 64  # fake old hash
    # Also clear tree_digest so we skip the short-circuit.
    state["tree_digest"] = "0" * 64
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    summary = update_template(target=target, force=False, dry_run=False)

    assert "AGENTS.md" in summary["conflicts"]
    # File must be preserved.
    assert agents_md.read_text(encoding="utf-8") == "# HOST EDITED\n"


def test_update_applies_updatable_file(tmp_path: Path) -> None:
    target = tmp_path / "host-updatable"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    agents_md = target / "AGENTS.md"
    real_hash = file_sha256(agents_md)

    # Simulate "template changed AGENTS.md since last install":
    # - set h_state = real_hash (host hasn't changed since install)
    # - write a *different* file content to the host AGENTS.md so h_host == real_hash,
    #   and the template hash (real) != h_state (fake_old).
    # Actually the simpler approach: write the old content to host and old hash to state,
    # then update will see h_host==h_state (host unchanged) but h_tpl != h_state (template changed).
    fake_old_content = "# OLD CONTENT\n"
    agents_md.write_text(fake_old_content, encoding="utf-8")
    fake_old_hash = file_sha256(agents_md)

    state_file = target / STATE_FILENAME
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["framework_manifest"]["AGENTS.md"]["sha256"] = fake_old_hash
    state["tree_digest"] = "0" * 64  # force full traversal
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    summary = update_template(target=target, force=False, dry_run=False)

    assert "AGENTS.md" in summary["updated"]
    # After update, the file should contain the real template content.
    assert file_sha256(agents_md) == real_hash


def test_manifest_as_map_normalises_legacy_list(tmp_path: Path) -> None:
    legacy = ["AGENTS.md", "ai/skills/foo.md"]
    result = _manifest_as_map(legacy)
    assert isinstance(result, dict)
    assert "AGENTS.md" in result
    assert result["AGENTS.md"]["ownership"] == "managed"
    assert result["AGENTS.md"]["sha256"] is None


def test_update_handles_legacy_list_manifest(tmp_path: Path) -> None:
    target = tmp_path / "host-legacy"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )

    # Downgrade manifest to legacy list format.
    state_file = target / STATE_FILENAME
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["framework_manifest"] = list(state["framework_manifest"].keys())
    state.pop("tree_digest", None)
    state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    # Update should succeed: legacy list normalised, then migrated to map format.
    summary = update_template(target=target, force=False, dry_run=False)
    # Legacy sha256=None means all entries treated as updatable (no sha256 to compare).
    # After update, state must have map-format manifest and tree_digest.
    new_state = json.loads(state_file.read_text(encoding="utf-8"))
    assert isinstance(new_state["framework_manifest"], dict)
    assert "tree_digest" in new_state


def test_classify_all_branches() -> None:
    assert _classify(None, "s", "t") == "missing"
    assert _classify("h", "h", "h") == "unchanged"
    assert _classify("h", "h", "T") == "updatable"
    assert _classify("H", "h", "h") == "locally-modified"
    assert _classify("H", "h", "T") == "conflict"
    # Legacy: h_state is None, host matches template → unchanged
    assert _classify("h", None, "h") == "unchanged"
    # Legacy: h_state is None, host differs from template → updatable
    assert _classify("h", None, "T") == "updatable"
