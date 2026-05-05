from __future__ import annotations

import sys
from pathlib import Path

from scripts.hooks import sync_dependencies


def test_pip_main_installs_profile_requirements(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.local.txt").write_text("pyyaml\n", encoding="utf-8")
    (tmp_path / "requirements.dev.txt").write_text("pytest\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["sync_dependencies.py", "--manager", "pip", "--profile", "local"]
    )

    sync_dependencies.main()

    assert calls == [
        [
            str(sync_dependencies.venv_python()),
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.local.txt",
            "-r",
            "requirements.dev.txt",
        ]
    ]


def test_uv_local_main_syncs_local_extra(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["sync_dependencies.py", "--manager", "uv", "--profile", "local"]
    )

    sync_dependencies.main()

    assert calls == [["uv", "sync", "--extra", "local"]]


def test_uv_cloud_main_syncs_local_and_cloud_extras(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["sync_dependencies.py", "--manager", "uv", "--profile", "cloud"]
    )

    sync_dependencies.main()

    assert calls == [["uv", "sync", "--extra", "local", "--extra", "cloud"]]


def test_main_skips_install_when_dependency_hash_is_unchanged(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    requirements = tmp_path / "requirements.local.txt"
    requirements.write_text("pyyaml\n", encoding="utf-8")
    current_hash = sync_dependencies.dependencies_hash(
        (Path("requirements.local.txt"),), "pip", "local"
    )
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / ".deps_hash").write_text(current_hash, encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        calls.append(command)

    monkeypatch.setattr(sync_dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["sync_dependencies.py", "--manager", "pip", "--profile", "local"]
    )

    sync_dependencies.main()

    assert calls == []
