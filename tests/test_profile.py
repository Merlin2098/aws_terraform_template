from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agents_framework.runtime.profile import (
    PROFILE_FILENAME,
    PROFILE_FILENAME_LEGACY,
    load_profile,
    profile_document,
    render_profile,
)


def _write_yaml(path: Path, content: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")


def test_load_profile_defaults_when_files_are_missing(tmp_path: Path) -> None:
    profile = load_profile(tmp_path)

    assert profile.capabilities == {}
    assert profile.dependency_policy.include_dev is True
    assert profile.source == "default"


def test_load_legacy_yaml_profile_reads_enabled_capabilities_and_policy(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path / PROFILE_FILENAME_LEGACY,
        {
            "schema_version": 1,
            "capabilities": {
                "languages": {"python": {"enabled": True}},
                "cloud": {"aws": {"enabled": False}},
            },
            "dependency_policy": {
                "include_dev": False,
                "additional_extras": ["custom"],
                "additional_groups": ["qa"],
            },
        },
    )

    profile = load_profile(tmp_path)

    assert profile.capabilities == {"languages": ["python"]}
    assert profile.declared_capabilities == {
        "languages": ["python"],
        "cloud": ["aws"],
    }
    assert profile.dependency_policy.include_dev is False
    assert profile.dependency_policy.manager == "uv"
    assert profile.dependency_policy.additional_extras == ("custom",)
    assert profile.dependency_policy.additional_groups == ("qa",)
    assert profile.source == "yaml-legacy"


def test_load_v2_yaml_profile_reads_flat_capabilities_list(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / PROFILE_FILENAME,
        {
            "schema_version": 2,
            "capabilities": {
                "enabled": ["languages:python", "cloud:aws"],
            },
            "dependencies": {
                "manager": "pip",
                "include_dev": False,
                "additional_extras": ["custom"],
            },
        },
    )

    profile = load_profile(tmp_path)

    assert profile.capabilities == {"languages": ["python"], "cloud": ["aws"]}
    assert profile.dependency_policy.include_dev is False
    assert profile.dependency_policy.manager == "pip"
    assert profile.dependency_policy.additional_extras == ("custom",)
    assert profile.source == "yaml"


def test_v2_profile_takes_precedence_over_legacy(tmp_path: Path) -> None:
    _write_yaml(
        tmp_path / PROFILE_FILENAME_LEGACY,
        {"schema_version": 1, "capabilities": {}},
    )
    _write_yaml(
        tmp_path / PROFILE_FILENAME,
        {"schema_version": 2, "capabilities": {"enabled": ["languages:python"]}},
    )

    profile = load_profile(tmp_path)

    assert profile.source == "yaml"
    assert "python" in profile.capabilities.get("languages", [])


@pytest.mark.parametrize(
    "document,match",
    [
        ({"schema_version": 99}, "schema_version"),
        (
            {
                "schema_version": 1,
                "capabilities": {"languages": {"python": {"enabled": "yes"}}},
            },
            "must be boolean",
        ),
        (
            {
                "schema_version": 1,
                "dependency_policy": {"include_dev": "yes"},
            },
            "include_dev",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": {"enabled": "not-a-list"},
            },
            "capabilities.enabled must be a list",
        ),
    ],
)
def test_invalid_yaml_profile_is_rejected(
    tmp_path: Path, document: dict[str, object], match: str
) -> None:
    _write_yaml(tmp_path / PROFILE_FILENAME, document)

    with pytest.raises(ValueError, match=match):
        load_profile(tmp_path)


def test_profile_document_contains_enabled_capabilities() -> None:
    registry = {
        "languages": {"python": object()},
        "cloud": {"aws": object()},
    }
    document = profile_document(
        registry,
        enabled={"languages": ["python"]},
    )
    rendered = render_profile(document)

    assert "languages:python" in rendered
    assert "cloud:aws" not in rendered
