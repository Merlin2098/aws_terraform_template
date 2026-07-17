from __future__ import annotations

import sys
from pathlib import Path

import agents_framework.tools.sync_deps as sync_deps_module
from scripts.hooks import sync_dependencies


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _sample_project(tmp_path: Path, *, cloud: bool = False) -> None:
    # pyproject.toml must declare extras matching real framework capabilities
    _write(
        tmp_path / "pyproject.toml",
        """[project]
name = "sample"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
local = []
cloud = []

[dependency-groups]
dev-local = []
dev-cloud = []
""",
    )
    # .template-profile.yaml (v1 legacy) sets manager="uv" automatically
    capability = (
        "  cloud:\n    aws:\n      enabled: true\n"
        if cloud
        else "  languages:\n    python:\n      enabled: true\n"
    )
    _write(
        tmp_path / ".template-profile.yaml",
        "schema_version: 1\ncapabilities:\n"
        f"{capability}"
        "dependency_policy:\n  include_dev: true\n"
        "  additional_extras: []\n  additional_groups: []\n",
    )


def test_local_main_syncs_resolved_extra_and_group(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _sample_project(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        sync_dependencies.subprocess,
        "run",
        lambda command, check: calls.append(command),
    )
    monkeypatch.setattr(sync_deps_module, "_manager_command_prefix", lambda m: ["uv"])
    monkeypatch.setattr(sys, "argv", ["sync_dependencies.py"])

    sync_dependencies.main()

    assert calls == [
        [
            "uv",
            "sync",
            "--no-default-groups",
            "--extra",
            "local",
            "--group",
            "dev-local",
        ]
    ]


def test_cloud_main_syncs_transitive_python_dependencies(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _sample_project(tmp_path, cloud=True)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        sync_dependencies.subprocess,
        "run",
        lambda command, check: calls.append(command),
    )
    monkeypatch.setattr(sync_deps_module, "_manager_command_prefix", lambda m: ["uv"])
    monkeypatch.setattr(sys, "argv", ["sync_dependencies.py"])

    sync_dependencies.main()

    assert calls[0] == [
        "uv",
        "sync",
        "--no-default-groups",
        "--extra",
        "local",
        "--extra",
        "cloud",
        "--group",
        "dev-local",
        "--group",
        "dev-cloud",
    ]


def test_dependency_hash_includes_capability_descriptors(tmp_path: Path) -> None:
    monkey_path = tmp_path / "ai/capabilities/cloud/aws.yaml"
    _write(monkey_path, "name: aws\n")

    first = sync_dependencies.dependencies_hash((monkey_path,))
    monkey_path.write_text("name: aws\nartifacts: [context_bundle]\n", encoding="utf-8")
    second = sync_dependencies.dependencies_hash((monkey_path,))

    assert first != second


def test_main_skips_install_when_hash_is_unchanged(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _sample_project(tmp_path)
    paths = sync_dependencies.dependency_files()
    current_hash = sync_dependencies.dependencies_hash(paths)
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv/.deps_hash").write_text(current_hash, encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(
        sync_dependencies.subprocess,
        "run",
        lambda command, check: calls.append(command),
    )
    monkeypatch.setattr(sys, "argv", ["sync_dependencies.py"])

    sync_dependencies.main()

    assert calls == []
