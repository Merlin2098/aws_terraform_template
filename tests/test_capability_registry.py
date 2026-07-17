from __future__ import annotations

from pathlib import Path

from agents_framework.runtime.capability_registry import (
    CapabilityDescriptor,
    active_paths,
    load_registry,
)


def test_load_registry_discovers_seeded_descriptors() -> None:
    registry = load_registry()

    assert "python" in registry["languages"]
    assert "aws" in registry["cloud"]
    assert "terraform" in registry["infrastructure"]
    assert "react" in registry["frameworks"]
    assert "saas" in registry["business"]


def test_load_registry_returns_all_categories_even_when_empty() -> None:
    registry = load_registry()

    for category in (
        "languages",
        "frameworks",
        "cloud",
        "infrastructure",
        "databases",
        "ai",
        "platform",
        "business",
        "operations",
    ):
        assert category in registry


def test_load_registry_accepts_legacy_root_argument(tmp_path: Path) -> None:
    # _legacy_root is accepted but ignored; capabilities always load from framework_root()
    registry = load_registry(tmp_path)

    assert isinstance(registry, dict)
    assert "languages" in registry
    assert "python" in registry["languages"]


def test_saas_descriptor_declares_saas_paths() -> None:
    registry = load_registry()
    saas = registry["business"]["saas"]

    assert "ai/skills/saas/" in saas.paths
    assert "ai/domains/saas.md" in saas.paths
    assert "saas" in saas.dependency_extras


def test_active_paths_unions_descriptor_paths() -> None:
    descriptors = [
        CapabilityDescriptor(name="a", category="languages", paths=["x", "y"]),
        CapabilityDescriptor(name="b", category="cloud", paths=["y", "z"]),
    ]

    assert active_paths(descriptors) == {"x", "y", "z"}
