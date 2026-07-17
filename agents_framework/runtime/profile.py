from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Current schema version for .agents-framework.yaml
PROFILE_SCHEMA_VERSION = 2
# Legacy schema version for .template-profile.yaml
PROFILE_SCHEMA_VERSION_LEGACY = 1

PROFILE_FILENAME = ".agents-framework.yaml"
PROFILE_FILENAME_LEGACY = ".template-profile.yaml"


@dataclass(frozen=True)
class DependencyPolicy:
    include_dev: bool = True
    manager: str = "pip"
    authority: str = "host"
    additional_extras: tuple[str, ...] = ()
    additional_groups: tuple[str, ...] = ()


@dataclass
class Profile:
    capabilities: dict[str, list[str]] = field(default_factory=dict)
    declared_capabilities: dict[str, list[str]] = field(default_factory=dict)
    dependency_policy: DependencyPolicy = field(default_factory=DependencyPolicy)
    precedence: dict[str, str] = field(default_factory=dict)
    overrides: dict[str, Any] = field(default_factory=dict)
    framework_source: str = ""
    schema_version: int = PROFILE_SCHEMA_VERSION
    source: str = "default"


def profile_path(project_root: Path) -> Path:
    return project_root / PROFILE_FILENAME


def _string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings.")
    return tuple(dict.fromkeys(item.strip() for item in value if item.strip()))


# ---------------------------------------------------------------------------
# Schema v2 parser (.agents-framework.yaml)
# ---------------------------------------------------------------------------


def _parse_v2_capabilities(
    enabled_list: list[str],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Parse the v2 flat ``capabilities.enabled`` list into (enabled, declared) maps."""
    enabled: dict[str, list[str]] = {}
    declared: dict[str, list[str]] = {}
    for entry in enabled_list:
        parts = entry.strip().split(":")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Capability '{entry}' must use the form category:name."
            )
        category, name = parts[0], parts[1]
        declared.setdefault(category, []).append(name)
        enabled.setdefault(category, []).append(name)
    return enabled, declared


def _load_v2_profile(path: Path, raw: dict[str, Any]) -> Profile:
    framework_block = raw.get("framework") or {}
    capabilities_block = raw.get("capabilities") or {}
    enabled_list = capabilities_block.get("enabled") or []
    if not isinstance(enabled_list, list):
        raise ValueError("capabilities.enabled must be a list.")
    enabled, declared = _parse_v2_capabilities(enabled_list)

    deps_block = raw.get("dependencies") or {}
    include_dev_raw = deps_block.get("include_dev", True)
    if not isinstance(include_dev_raw, bool):
        raise ValueError("dependencies.include_dev must be boolean.")
    additional_extras = _string_list(
        deps_block.get("additional_extras"), "dependencies.additional_extras"
    )
    additional_groups = _string_list(
        deps_block.get("additional_groups"), "dependencies.additional_groups"
    )

    precedence = raw.get("precedence") or {}
    overrides = raw.get("overrides") or {}

    return Profile(
        capabilities=enabled,
        declared_capabilities=declared,
        dependency_policy=DependencyPolicy(
            include_dev=include_dev_raw,
            manager=str(deps_block.get("manager", "pip")),
            authority=str(deps_block.get("authority", "host")),
            additional_extras=additional_extras,
            additional_groups=additional_groups,
        ),
        precedence=dict(precedence),
        overrides=dict(overrides),
        framework_source=str(framework_block.get("source", "")),
        schema_version=PROFILE_SCHEMA_VERSION,
        source="yaml",
    )


# ---------------------------------------------------------------------------
# Schema v1 parser (.template-profile.yaml, backward compat)
# ---------------------------------------------------------------------------


def _parse_v1_capabilities(
    value: Any,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    if value is None:
        return {}, {}
    if not isinstance(value, dict):
        raise ValueError("capabilities must be a mapping.")

    enabled: dict[str, list[str]] = {}
    declared: dict[str, list[str]] = {}
    for raw_category, raw_entries in value.items():
        category = str(raw_category).strip()
        if not category or not isinstance(raw_entries, dict):
            raise ValueError(f"capabilities.{category or '<empty>'} must be a mapping.")
        for raw_name, raw_config in raw_entries.items():
            name = str(raw_name).strip()
            if not name or not isinstance(raw_config, dict):
                raise ValueError(
                    f"capabilities.{category}.{name or '<empty>'} must be a mapping."
                )
            declared.setdefault(category, []).append(name)
            is_enabled = raw_config.get("enabled", False)
            if not isinstance(is_enabled, bool):
                raise ValueError(
                    f"capabilities.{category}.{name}.enabled must be boolean."
                )
            if is_enabled:
                enabled.setdefault(category, []).append(name)
    return enabled, declared


def _load_v1_profile(path: Path, raw: dict[str, Any]) -> Profile:
    raw_policy = raw.get("dependency_policy") or {}
    if not isinstance(raw_policy, dict):
        raise ValueError("dependency_policy must be a mapping.")
    include_dev = raw_policy.get("include_dev", True)
    if not isinstance(include_dev, bool):
        raise ValueError("dependency_policy.include_dev must be boolean.")

    capabilities, declared_capabilities = _parse_v1_capabilities(
        raw.get("capabilities")
    )
    return Profile(
        capabilities=capabilities,
        declared_capabilities=declared_capabilities,
        dependency_policy=DependencyPolicy(
            include_dev=include_dev,
            manager="uv",
            authority="host",
            additional_extras=_string_list(
                raw_policy.get("additional_extras"),
                "dependency_policy.additional_extras",
            ),
            additional_groups=_string_list(
                raw_policy.get("additional_groups"),
                "dependency_policy.additional_groups",
            ),
        ),
        schema_version=PROFILE_SCHEMA_VERSION_LEGACY,
        source="yaml-legacy",
    )


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------


def _load_yaml_profile(path: Path) -> Profile:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path.name}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping.")

    schema_version = raw.get("schema_version")
    if schema_version == PROFILE_SCHEMA_VERSION:
        return _load_v2_profile(path, raw)
    if schema_version == PROFILE_SCHEMA_VERSION_LEGACY:
        return _load_v1_profile(path, raw)
    raise ValueError(
        f"Unsupported profile schema_version {schema_version!r}; "
        f"expected {PROFILE_SCHEMA_VERSION} (or {PROFILE_SCHEMA_VERSION_LEGACY} for legacy)."
    )


def load_profile(path_or_root: Path) -> Profile:
    """Load the active profile, preferring .agents-framework.yaml over legacy format."""
    if path_or_root.is_dir():
        v2_path = path_or_root / PROFILE_FILENAME
        if v2_path.exists():
            return _load_yaml_profile(v2_path)
        legacy_path = path_or_root / PROFILE_FILENAME_LEGACY
        if legacy_path.exists():
            return _load_yaml_profile(legacy_path)
        return Profile()

    if path_or_root.exists():
        return _load_yaml_profile(path_or_root)
    return Profile()


# ---------------------------------------------------------------------------
# Rendering (used when generating .agents-framework.yaml for a new host)
# ---------------------------------------------------------------------------


def profile_document(
    registry: dict[str, dict[str, Any]],
    *,
    enabled: dict[str, list[str]],
    include_dev: bool = True,
    manager: str = "pip",
    additional_extras: tuple[str, ...] = (),
    additional_groups: tuple[str, ...] = (),
    framework_source: str = "",
) -> dict[str, Any]:
    enabled_list = [
        f"{category}:{name}"
        for category in sorted(registry)
        for name in sorted(registry[category])
        if name in enabled.get(category, [])
    ]
    doc: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "capabilities": {"enabled": enabled_list},
        "precedence": {
            "conventions": "host-first",
            "safety": "framework-required",
        },
        "overrides": {"skills": {}, "policies": {}},
        "dependencies": {
            "manager": manager,
            "authority": "host",
            "include_dev": include_dev,
            "additional_extras": list(additional_extras),
        },
    }
    if framework_source:
        doc["framework"] = {"source": framework_source}
    return doc


def render_profile(document: dict[str, Any]) -> str:
    return yaml.safe_dump(
        document,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
