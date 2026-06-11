from __future__ import annotations

import sys
from pathlib import Path

from scripts.hooks import sync_dependencies


def test_uv_local_main_syncs_base_only_plus_local_dev_group(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(sync_dependencies, "uv_command_prefix", lambda: ["uv"])
    monkeypatch.setattr(sys, "argv", ["sync_dependencies.py", "--profile", "local"])

    sync_dependencies.main()

    assert calls == [["uv", "sync", "--group", "dev-local"]]


def test_uv_cloud_main_syncs_local_and_cloud_extras(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(sync_dependencies, "uv_command_prefix", lambda: ["uv"])
    monkeypatch.setattr(sys, "argv", ["sync_dependencies.py", "--profile", "cloud"])

    sync_dependencies.main()

    assert calls == [
        [
            "uv",
            "sync",
            "--extra",
            "local",
            "--extra",
            "cloud",
            "--group",
            "dev-local",
            "--group",
            "dev-cloud",
        ]
    ]


def test_uv_command_prefix_uses_py_launcher_on_windows(monkeypatch) -> None:
    monkeypatch.setattr(
        sync_dependencies.shutil,
        "which",
        lambda name: None if name == "uv" else "C:/Windows/py.exe",
    )
    monkeypatch.setattr(sync_dependencies.sys, "platform", "win32")

    assert sync_dependencies.uv_command_prefix() == ["py", "-3", "-m", "uv"]


def test_main_skips_install_when_dependency_hash_is_unchanged(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='x'\n", encoding="utf-8")
    current_hash = sync_dependencies.dependencies_hash(
        (Path("pyproject.toml"),), "local"
    )
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / ".deps_hash").write_text(current_hash, encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["sync_dependencies.py", "--profile", "local"])

    sync_dependencies.main()

    assert calls == []
