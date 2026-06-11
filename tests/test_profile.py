from __future__ import annotations

from pathlib import Path

from ai.runtime.profile import (
    Profile,
    load_profile,
    resolve_environment_profile,
)


def test_load_profile_missing_file_returns_empty_profile(tmp_path: Path) -> None:
    profile = load_profile(tmp_path / ".template-profile")

    assert profile == Profile()


def test_load_profile_legacy_fields(tmp_path: Path) -> None:
    profile_file = tmp_path / ".template-profile"
    profile_file.write_text(
        "package_manager=uv\nenvironment_profile=cloud\ncapability_profile=\n",
        encoding="utf-8",
    )

    profile = load_profile(profile_file)

    assert profile.package_manager == "uv"
    assert profile.environment_profile == "cloud"
    assert profile.capabilities == {}


def test_load_profile_legacy_capability_profile_normalizes_to_typed_block(
    tmp_path: Path,
) -> None:
    profile_file = tmp_path / ".template-profile"
    profile_file.write_text(
        "package_manager=uv\nenvironment_profile=cloud\ncapability_profile=saas\n",
        encoding="utf-8",
    )

    profile = load_profile(profile_file)

    assert profile.capabilities == {"business": ["saas"]}


def test_load_profile_typed_capabilities_block_takes_precedence(
    tmp_path: Path,
) -> None:
    profile_file = tmp_path / ".template-profile"
    profile_file.write_text(
        "package_manager=uv\n"
        "environment_profile=cloud\n"
        "capability_profile=saas\n"
        "capabilities:\n"
        "  business:\n"
        "    - saas\n"
        "  languages:\n"
        "    - python\n"
        "    - golang\n",
        encoding="utf-8",
    )

    profile = load_profile(profile_file)

    assert profile.capabilities == {
        "business": ["saas"],
        "languages": ["python", "golang"],
    }


def test_load_profile_invalid_environment_profile_is_ignored(tmp_path: Path) -> None:
    profile_file = tmp_path / ".template-profile"
    profile_file.write_text("environment_profile=staging\n", encoding="utf-8")

    profile = load_profile(profile_file)

    assert profile.environment_profile is None


def test_resolve_environment_profile_prefers_selected(tmp_path: Path) -> None:
    profile_file = tmp_path / ".template-profile"
    profile_file.write_text("environment_profile=cloud\n", encoding="utf-8")

    assert resolve_environment_profile(profile_file, "local") == "local"


def test_resolve_environment_profile_falls_back_to_persisted(tmp_path: Path) -> None:
    profile_file = tmp_path / ".template-profile"
    profile_file.write_text("environment_profile=cloud\n", encoding="utf-8")

    assert resolve_environment_profile(profile_file, None) == "cloud"


def test_resolve_environment_profile_defaults_to_local(tmp_path: Path) -> None:
    profile_file = tmp_path / ".template-profile"

    assert resolve_environment_profile(profile_file, None) == "local"
