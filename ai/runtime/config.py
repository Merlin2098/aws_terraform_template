from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_context_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root.resolve() / "ai" / "context.yaml"
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Invalid AI context config at {config_path}")
    return loaded


def artifact_paths(config: dict[str, Any]) -> list[str]:
    return _string_list(config.get("artifacts"))


def ignore_dirs(config: dict[str, Any]) -> set[str]:
    return set(_string_list(config.get("ignore_dirs")))


def ignore_top_level_files(config: dict[str, Any]) -> set[str]:
    return set(_string_list(config.get("ignore_top_level_files")))


def structure_map(config: dict[str, Any]) -> dict[str, list[str]]:
    raw = _mapping(config.get("structure"))
    return {str(key): _string_list(value) for key, value in raw.items()}


def rules_list(config: dict[str, Any]) -> list[str]:
    return _string_list(config.get("rules"))


def _roots(config: dict[str, Any], key: str) -> dict[str, list[str]]:
    raw = _mapping(config.get(key))
    return {
        "files": _string_list(raw.get("files")),
        "directories": _string_list(raw.get("directories")),
    }


def entrypoint_roots(config: dict[str, Any]) -> dict[str, list[str]]:
    return _roots(config, "entrypoint_roots")


def module_roots(config: dict[str, Any]) -> dict[str, list[str]]:
    return _roots(config, "module_roots")
