from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ai.runtime.capability_registry import normalize_capabilities


ENVIRONMENT_PROFILES = {"local", "cloud"}
PACKAGE_MANAGERS = {"pip", "uv"}
DEFAULT_ENVIRONMENT_PROFILE = "local"


@dataclass
class Profile:
    """Normalized view of a host's `.template-profile` file.

    Combines the legacy fields (`package_manager`, `environment_profile`,
    `capability_profile`) with the typed `capabilities:` block from
    ADR-FW-001. Legacy `capability_profile=<value>` is folded into
    `capabilities` so callers only need to read one shape.
    """

    environment_profile: str | None = None
    package_manager: str | None = None
    capabilities: dict[str, list[str]] = field(default_factory=dict)


def _parse_template_profile(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values


def load_profile(profile_file: Path) -> Profile:
    """Read and normalize a `.template-profile` file.

    Returns an empty `Profile` if the file does not exist. Supports both the
    legacy `key=value` format and a typed `capabilities:` block written in
    YAML mapping syntax (`category:\\n  - name`), per ADR-FW-001's
    Compatibility Strategy.
    """
    if not profile_file.exists():
        return Profile()

    text = profile_file.read_text(encoding="utf-8")
    values = _parse_template_profile(text)

    environment_profile = values.get("environment_profile", "").strip().lower() or None
    if environment_profile not in ENVIRONMENT_PROFILES:
        environment_profile = None

    package_manager = values.get("package_manager", "").strip().lower() or None
    if package_manager not in PACKAGE_MANAGERS:
        package_manager = None

    capabilities = _load_capabilities_block(text)
    if not capabilities:
        legacy_capability_profile = values.get("capability_profile", "").strip().lower()
        if legacy_capability_profile:
            capabilities = normalize_capabilities([legacy_capability_profile])

    return Profile(
        environment_profile=environment_profile,
        package_manager=package_manager,
        capabilities=capabilities,
    )


def _load_capabilities_block(text: str) -> dict[str, list[str]]:
    """Parse a trailing YAML `capabilities:` block, if present.

    `.template-profile` is primarily `key=value`, but ADR-FW-001 allows an
    additional typed `capabilities:` mapping appended to the file. Lines
    using `=` are not valid YAML mappings, so only lines that are not legacy
    `key=value` pairs are considered for YAML parsing.
    """
    yaml_lines = [
        line
        for line in text.splitlines()
        if line.strip() and "=" not in line.split("#", 1)[0]
    ]
    if not yaml_lines:
        return {}

    try:
        loaded = yaml.safe_load("\n".join(yaml_lines))
    except yaml.YAMLError:
        return {}

    if not isinstance(loaded, dict):
        return {}

    return normalize_capabilities(loaded.get("capabilities"))


def resolve_environment_profile(profile_file: Path, selected: str | None) -> str:
    """Resolve the active environment profile.

    Precedence: explicitly `selected` > value persisted in `profile_file` >
    `DEFAULT_ENVIRONMENT_PROFILE`. Mirrors the previous
    `resolve_profile` helpers duplicated in `scripts/run_uv_sync.py` and
    `scripts/hooks/sync_dependencies.py`.
    """
    if selected:
        return selected
    persisted = load_profile(profile_file).environment_profile
    if persisted:
        return persisted
    return DEFAULT_ENVIRONMENT_PROFILE
