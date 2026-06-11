from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROFILE_FILENAME = ".template-profile.yaml"
PROFILE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class DependencyPolicy:
    include_dev: bool = True
    additional_extras: tuple[str, ...] = ()
    additional_groups: tuple[str, ...] = ()


@dataclass
class Profile:
    capabilities: dict[str, list[str]] = field(default_factory=dict)
    declared_capabilities: dict[str, list[str]] = field(default_factory=dict)
    dependency_policy: DependencyPolicy = field(default_factory=DependencyPolicy)
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


def _parse_yaml_capabilities(
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
            unknown = set(raw_config) - {"enabled"}
            if unknown:
                raise ValueError(
                    f"capabilities.{category}.{name} has unknown fields: "
                    f"{', '.join(sorted(unknown))}."
                )
            is_enabled = raw_config.get("enabled", False)
            if not isinstance(is_enabled, bool):
                raise ValueError(
                    f"capabilities.{category}.{name}.enabled must be boolean."
                )
            if is_enabled:
                enabled.setdefault(category, []).append(name)
    return enabled, declared


def _load_yaml_profile(path: Path) -> Profile:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path.name}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping.")

    allowed = {
        "schema_version",
        "capabilities",
        "dependency_policy",
    }
    unknown = set(loaded) - allowed
    if unknown:
        raise ValueError(
            f"{path.name} has unknown fields: {', '.join(sorted(unknown))}."
        )

    schema_version = loaded.get("schema_version")
    if schema_version != PROFILE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported profile schema_version {schema_version!r}; "
            f"expected {PROFILE_SCHEMA_VERSION}."
        )

    raw_policy = loaded.get("dependency_policy") or {}
    if not isinstance(raw_policy, dict):
        raise ValueError("dependency_policy must be a mapping.")
    policy_unknown = set(raw_policy) - {
        "include_dev",
        "additional_extras",
        "additional_groups",
    }
    if policy_unknown:
        raise ValueError(
            "dependency_policy has unknown fields: "
            f"{', '.join(sorted(policy_unknown))}."
        )
    include_dev = raw_policy.get("include_dev", True)
    if not isinstance(include_dev, bool):
        raise ValueError("dependency_policy.include_dev must be boolean.")

    capabilities, declared_capabilities = _parse_yaml_capabilities(
        loaded.get("capabilities")
    )
    return Profile(
        capabilities=capabilities,
        declared_capabilities=declared_capabilities,
        dependency_policy=DependencyPolicy(
            include_dev=include_dev,
            additional_extras=_string_list(
                raw_policy.get("additional_extras"),
                "dependency_policy.additional_extras",
            ),
            additional_groups=_string_list(
                raw_policy.get("additional_groups"),
                "dependency_policy.additional_groups",
            ),
        ),
        source="yaml",
    )


def load_profile(path_or_root: Path) -> Profile:
    """Load the active YAML profile."""
    candidate = path_or_root
    if candidate.is_dir():
        yaml_path = profile_path(candidate)
    elif candidate.name == PROFILE_FILENAME:
        yaml_path = candidate
    else:
        yaml_path = candidate / PROFILE_FILENAME

    if yaml_path.exists():
        return _load_yaml_profile(yaml_path)
    return Profile()


def profile_document(
    registry: dict[str, dict[str, Any]],
    *,
    enabled: dict[str, list[str]],
    include_dev: bool = True,
    additional_extras: tuple[str, ...] = (),
    additional_groups: tuple[str, ...] = (),
) -> dict[str, Any]:
    capabilities: dict[str, dict[str, dict[str, bool]]] = {}
    for category in sorted(registry):
        entries = registry[category]
        if not entries:
            continue
        enabled_names = set(enabled.get(category, []))
        capabilities[category] = {
            name: {"enabled": name in enabled_names} for name in sorted(entries)
        }
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "capabilities": capabilities,
        "dependency_policy": {
            "include_dev": include_dev,
            "additional_extras": list(additional_extras),
            "additional_groups": list(additional_groups),
        },
    }


def render_profile(document: dict[str, Any]) -> str:
    return yaml.safe_dump(
        document,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
