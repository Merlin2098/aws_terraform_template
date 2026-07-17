from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agents_framework import framework_root


CAPABILITY_CATEGORIES = (
    "languages",
    "frameworks",
    "cloud",
    "infrastructure",
    "databases",
    "ai",
    "platform",
    "business",
    "operations",
)

CAPABILITIES_DIRNAME = "capabilities"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


@dataclass
class CapabilityDescriptor:
    name: str
    category: str
    type: str | None = None
    depends_on: dict[str, list[str]] = field(default_factory=dict)
    paths: list[str] = field(default_factory=list)
    dependency_extras: list[str] = field(default_factory=list)
    dependency_groups: list[str] = field(default_factory=list)
    scanners: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)


def _capabilities_root() -> Path:
    return framework_root() / CAPABILITIES_DIRNAME


def _load_descriptor(path: Path, category: str) -> CapabilityDescriptor:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        loaded = {}

    depends_on_raw = _mapping(loaded.get("depends_on"))
    dependencies_raw = _mapping(loaded.get("dependencies"))

    return CapabilityDescriptor(
        name=str(loaded.get("name") or path.stem).strip(),
        category=category,
        type=str(loaded["type"]).strip() if loaded.get("type") else None,
        depends_on={
            str(key): _string_list(value) for key, value in depends_on_raw.items()
        },
        paths=_string_list(loaded.get("paths")),
        dependency_extras=_string_list(dependencies_raw.get("extras")),
        dependency_groups=_string_list(dependencies_raw.get("groups")),
        scanners=_string_list(loaded.get("scanners")),
        hooks=_string_list(loaded.get("hooks")),
        artifacts=_string_list(loaded.get("artifacts")),
    )


def load_registry(
    _legacy_root: Path | None = None,
) -> dict[str, dict[str, CapabilityDescriptor]]:
    """Load all capability descriptors grouped by category then name.

    The ``_legacy_root`` parameter is accepted but ignored; capabilities are
    always loaded from the installed framework package (``framework_root()``).
    It is kept for backward compatibility with callers that previously passed
    ``template_root``.
    """
    registry: dict[str, dict[str, CapabilityDescriptor]] = {
        category: {} for category in CAPABILITY_CATEGORIES
    }

    capabilities_root = _capabilities_root()
    if not capabilities_root.is_dir():
        return registry

    for category_dir in sorted(capabilities_root.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        registry.setdefault(category, {})
        for descriptor_path in sorted(category_dir.glob("*.yaml")):
            descriptor = _load_descriptor(descriptor_path, category)
            registry[category][descriptor.name] = descriptor

    return registry


def active_paths(descriptors: list[CapabilityDescriptor]) -> set[str]:
    """Union of all ``paths`` declared by the given descriptors."""
    paths: set[str] = set()
    for descriptor in descriptors:
        paths.update(descriptor.paths)
    return paths
