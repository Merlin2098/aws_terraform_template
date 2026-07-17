from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from agents_framework.runtime.capability_registry import CapabilityDescriptor, load_registry
from agents_framework.runtime.profile import Profile, load_profile


@dataclass(frozen=True)
class ResolvedProfile:
    profile: Profile
    explicit_capabilities: tuple[str, ...]
    implicit_capabilities: tuple[str, ...]
    disabled_capabilities: tuple[str, ...]
    descriptors: tuple[CapabilityDescriptor, ...]
    extras: tuple[str, ...]
    groups: tuple[str, ...]
    paths: tuple[str, ...]
    scanners: tuple[str, ...]
    hooks: tuple[str, ...]
    artifacts: tuple[str, ...]

    @property
    def active_capabilities(self) -> tuple[str, ...]:
        return self.explicit_capabilities + self.implicit_capabilities


def capability_id(category: str, name: str) -> str:
    return f"{category}:{name}"


def parse_capability_id(value: str) -> tuple[str, str]:
    category, separator, name = value.strip().partition(":")
    if not separator or not category or not name:
        raise ValueError(f"Capability '{value}' must use the form category:name.")
    return category, name


def _append_unique(values: list[str], additions: list[str] | tuple[str, ...]) -> None:
    for value in additions:
        if value not in values:
            values.append(value)


def _host_extras(project_root: Path) -> set[str]:
    """Return the set of optional-dependency extras declared in pyproject.toml, if present."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return set()
    with pyproject.open("rb") as handle:
        loaded = tomllib.load(handle)
    project = loaded.get("project") or {}
    return set((project.get("optional-dependencies") or {}).keys())


def _host_groups(project_root: Path) -> set[str]:
    """Return dependency-groups declared in pyproject.toml, if present."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return set()
    with pyproject.open("rb") as handle:
        loaded = tomllib.load(handle)
    return set((loaded.get("dependency-groups") or {}).keys())


def resolve_project_profile(
    project_root: Path,
    *,
    profile: Profile | None = None,
    validate_dependencies: bool = True,
) -> ResolvedProfile:
    project_root = project_root.resolve()
    profile = profile or load_profile(project_root)
    registry = load_registry()

    explicit: list[str] = []
    implicit: list[str] = []
    descriptors: list[CapabilityDescriptor] = []
    resolved_ids: set[str] = set()
    visiting: list[str] = []

    declared = profile.declared_capabilities or profile.capabilities
    expected_types = {
        "languages": "language",
        "frameworks": "framework",
        "cloud": "cloud",
        "infrastructure": "infrastructure",
        "databases": "database",
        "ai": "ai",
        "platform": "platform",
        "business": "business",
        "operations": "operation",
    }
    for category, names in declared.items():
        if category not in registry:
            raise ValueError(f"Unknown capability category '{category}'.")
        for name in names:
            if name not in registry[category]:
                raise ValueError(f"Unknown capability '{category}:{name}'.")
            descriptor = registry[category][name]
            expected_type = expected_types.get(category)
            if descriptor.type and expected_type and descriptor.type != expected_type:
                raise ValueError(
                    f"Capability '{category}:{name}' has type "
                    f"'{descriptor.type}', expected '{expected_type}'."
                )

    for category, names in profile.capabilities.items():
        for name in names:
            _append_unique(explicit, [capability_id(category, name)])

    def visit(category: str, name: str, *, is_explicit: bool) -> None:
        identifier = capability_id(category, name)
        if identifier in resolved_ids:
            return
        if identifier in visiting:
            cycle = " -> ".join([*visiting, identifier])
            raise ValueError(f"Capability dependency cycle detected: {cycle}.")
        descriptor = registry.get(category, {}).get(name)
        if descriptor is None:
            raise ValueError(f"Unknown capability dependency '{identifier}'.")
        expected_type = expected_types.get(category)
        if descriptor.type and expected_type and descriptor.type != expected_type:
            raise ValueError(
                f"Capability '{identifier}' has type '{descriptor.type}', "
                f"expected '{expected_type}'."
            )

        visiting.append(identifier)
        for dependency_category, dependency_names in descriptor.depends_on.items():
            for dependency_name in dependency_names:
                visit(dependency_category, dependency_name, is_explicit=False)
        visiting.pop()

        resolved_ids.add(identifier)
        descriptors.append(descriptor)
        if not is_explicit and identifier not in explicit:
            _append_unique(implicit, [identifier])

    for identifier in explicit:
        category, name = parse_capability_id(identifier)
        visit(category, name, is_explicit=True)

    extras: list[str] = []
    groups: list[str] = []
    paths: list[str] = []
    scanners: list[str] = []
    hooks: list[str] = []
    artifacts: list[str] = []
    for descriptor in descriptors:
        _append_unique(extras, descriptor.dependency_extras)
        if profile.dependency_policy.include_dev:
            _append_unique(groups, descriptor.dependency_groups)
        _append_unique(paths, descriptor.paths)
        _append_unique(scanners, descriptor.scanners)
        _append_unique(hooks, descriptor.hooks)
        _append_unique(artifacts, descriptor.artifacts)

    _append_unique(extras, profile.dependency_policy.additional_extras)
    if profile.dependency_policy.include_dev:
        _append_unique(groups, profile.dependency_policy.additional_groups)

    if validate_dependencies and profile.dependency_policy.manager != "npm":
        available_extras = _host_extras(project_root)
        available_groups = _host_groups(project_root)
        if available_extras:
            missing_extras = sorted(set(extras) - available_extras)
            if missing_extras:
                raise ValueError(
                    f"unknown pyproject extras: {', '.join(missing_extras)}"
                )
        if available_groups:
            missing_groups = sorted(set(groups) - available_groups)
            if missing_groups:
                raise ValueError(
                    f"unknown dependency groups: {', '.join(missing_groups)}"
                )

    all_ids = {
        capability_id(category, name)
        for category, entries in registry.items()
        for name in entries
    }
    disabled = tuple(sorted(all_ids - resolved_ids))
    return ResolvedProfile(
        profile=profile,
        explicit_capabilities=tuple(explicit),
        implicit_capabilities=tuple(implicit),
        disabled_capabilities=disabled,
        descriptors=tuple(descriptors),
        extras=tuple(extras),
        groups=tuple(groups),
        paths=tuple(paths),
        scanners=tuple(scanners),
        hooks=tuple(hooks),
        artifacts=tuple(artifacts),
    )


def pip_install_args(resolved: ResolvedProfile, *, editable: bool = True) -> list[str]:
    """Generate ``pip install`` arguments for the resolved extras."""
    flag = "-e" if editable else ""
    if not resolved.extras:
        target = "." if editable else "."
        return ["install", "-e", target] if editable else ["install", target]
    extras_str = ",".join(resolved.extras)
    target = f".[{extras_str}]"
    args = ["install"]
    if editable:
        args.append("-e")
    args.append(target)
    return args


def uv_sync_args(resolved: ResolvedProfile, *, locked: bool = False) -> list[str]:
    """Generate ``uv sync`` arguments (kept for backward compatibility and uv hosts)."""
    args = ["sync", "--no-default-groups"]
    if locked:
        args.append("--locked")
    for extra in resolved.extras:
        args.extend(["--extra", extra])
    for group in resolved.groups:
        args.extend(["--group", group])
    return args


def uv_export_args(resolved: ResolvedProfile) -> list[str]:
    args = ["export", "--no-dev", "--format", "requirements.txt"]
    for extra in resolved.extras:
        args.extend(["--extra", extra])
    return args
