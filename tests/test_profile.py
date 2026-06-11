from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ai.runtime.profile import (
    PROFILE_FILENAME,
    load_profile,
    profile_document,
    render_profile,
)


def _write_yaml(path: Path, content: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")


def test_load_profile_defaults_when_files_are_missing(tmp_path: Path) -> None:
    profile = load_profile(tmp_path)

    assert profile.environment == "local"
    assert profile.capabilities == {}
    assert profile.dependency_policy.include_dev is True
    assert profile.source == "default"


def test_load_yaml_profile_reads_enabled_capabilities_and_policy(
    tmp_path: Path,
) -> None:
    _write_yaml(
        tmp_path / PROFILE_FILENAME,
        {
            "schema_version": 1,
            "environment": "cloud",
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

    assert profile.environment == "cloud"
    assert profile.capabilities == {"languages": ["python"]}
    assert profile.declared_capabilities == {
        "languages": ["python"],
        "cloud": ["aws"],
    }
    assert profile.dependency_policy.include_dev is False
    assert profile.dependency_policy.additional_extras == ("custom",)
    assert profile.dependency_policy.additional_groups == ("qa",)
    assert profile.source == "yaml"


@pytest.mark.parametrize(
    "document,match",
    [
        ({"schema_version": 2}, "schema_version"),
        (
            {"schema_version": 1, "environment": "staging"},
            "environment",
        ),
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
    ],
)
def test_invalid_yaml_profile_is_rejected(
    tmp_path: Path, document: dict[str, object], match: str
) -> None:
    _write_yaml(tmp_path / PROFILE_FILENAME, document)

    with pytest.raises(ValueError, match=match):
        load_profile(tmp_path)


def test_profile_document_contains_full_catalog() -> None:
    registry = {
        "languages": {"python": object()},
        "cloud": {"aws": object()},
    }
    document = profile_document(
        registry,
        environment="local",
        enabled={"languages": ["python"]},
    )
    rendered = render_profile(document)

    assert "python:\n      enabled: true" in rendered
    assert "aws:\n      enabled: false" in rendered
