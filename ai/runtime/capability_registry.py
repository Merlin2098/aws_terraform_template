from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


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

# Legacy `capability_profile=<value>` (SPEC-FW-004) normalizes into this
# category, per ADR-FW-001's Compatibility Strategy.
LEGACY_CAPABILITY_PROFILE_CATEGORY = "business"


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


def _capabilities_root(template_root: Path) -> Path:
    return template_root / "ai" / CAPABILITIES_DIRNAME


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
    template_root: Path,
) -> dict[str, dict[str, CapabilityDescriptor]]:
    """Load all capability descriptors, grouped by category then name."""
    registry: dict[str, dict[str, CapabilityDescriptor]] = {
        category: {} for category in CAPABILITY_CATEGORIES
    }

    capabilities_root = _capabilities_root(template_root)
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


def normalize_capabilities(raw: Any) -> dict[str, list[str]]:
    """Normalize a capabilities value into the typed ``{category: [names]}`` shape.

    Accepts, per ADR-FW-001's Compatibility Strategy:

    - The typed block: ``{category: [names], ...}`` (returned as-is, sorted).
    - A flat legacy list: ``[name, ...]`` (placed under
      ``LEGACY_CAPABILITY_PROFILE_CATEGORY``).
    - ``None`` / empty (returns an empty mapping).
    """
    if isinstance(raw, dict):
        normalized: dict[str, list[str]] = {}
        for category, values in raw.items():
            names = _string_list(values)
            if names:
                normalized[str(category).strip()] = names
        return normalized

    flat = _string_list(raw)
    if not flat:
        return {}
    return {LEGACY_CAPABILITY_PROFILE_CATEGORY: flat}


def resolve_descriptors(
    registry: dict[str, dict[str, CapabilityDescriptor]],
    capabilities: dict[str, list[str]],
) -> list[CapabilityDescriptor]:
    """Resolve the active capability selection into descriptors.

    Unknown category/name combinations are skipped silently — the registry is
    additive and a host's `.template-profile` may reference capabilities that
    have not been migrated to a descriptor yet.
    """
    resolved: list[CapabilityDescriptor] = []
    for category, names in capabilities.items():
        category_registry = registry.get(category, {})
        for name in names:
            descriptor = category_registry.get(name)
            if descriptor is not None:
                resolved.append(descriptor)
    return resolved


def active_paths(descriptors: list[CapabilityDescriptor]) -> set[str]:
    """Union of all ``paths`` declared by the given descriptors."""
    paths: set[str] = set()
    for descriptor in descriptors:
        paths.update(descriptor.paths)
    return paths


def category_paths(
    registry: dict[str, dict[str, CapabilityDescriptor]], category: str
) -> set[str]:
    """Union of all ``paths`` declared by every descriptor in ``category``."""
    return active_paths(list(registry.get(category, {}).values()))
