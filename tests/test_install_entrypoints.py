from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ai.installer import STATE_FILENAME, install_template


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_installer(
    script: str, target: Path, *args: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            script,
            "--target",
            str(target),
            "--dry-run",
            "--without-structure",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


def _run_update(
    script: str, target: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            script,
            "--target",
            str(target),
            "--update",
            "--without-structure",
            "--dry-run",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_windows_installer_accepts_repeatable_capabilities(tmp_path: Path) -> None:
    target = tmp_path / "windows-host"

    result = _run_installer(
        "install_windows.py",
        target,
        "--enable",
        "business:saas",
        "--enable",
        "databases:supabase",
    )

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout
    assert not target.exists()


def test_linux_installer_accepts_none_selection(tmp_path: Path) -> None:
    target = tmp_path / "linux-host"

    result = _run_installer("install_linux.py", target, "--enable", "none")

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout
    assert not target.exists()


def test_empty_interactive_selection_enables_all_capabilities(tmp_path: Path) -> None:
    result = _run_installer(
        "install_linux.py",
        tmp_path / "host",
        input_text="\n",
    )

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout


def test_installers_reject_removed_environment_shortcuts(tmp_path: Path) -> None:
    result = _run_installer("install_linux.py", tmp_path / "host", "--local")

    assert result.returncode != 0
    assert "unrecognized arguments: --local" in result.stderr


def test_windows_update_on_installed_host_succeeds(tmp_path: Path) -> None:
    target = tmp_path / "windows-update-host"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    assert (target / STATE_FILENAME).exists()

    result = _run_update("install_windows.py", target)

    assert result.returncode == 0, result.stderr
    assert "summary" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout


def test_linux_update_on_installed_host_succeeds(tmp_path: Path) -> None:
    target = tmp_path / "linux-update-host"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    assert (target / STATE_FILENAME).exists()

    result = _run_update("install_linux.py", target)

    assert result.returncode == 0, result.stderr
    assert "summary" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout


def test_update_without_prior_install_exits_with_error(tmp_path: Path) -> None:
    target = tmp_path / "no-state-host"
    target.mkdir()

    for script in ("install_windows.py", "install_linux.py"):
        result = _run_update(script, target)
        assert result.returncode != 0, f"{script} should fail without prior install"
        assert "No framework state found" in result.stderr or "error" in result.stderr.lower()


def test_installer_auto_detects_existing_installation_and_updates(tmp_path: Path) -> None:
    target = tmp_path / "auto-detect-host"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    assert (target / STATE_FILENAME).exists()

    # Run the plain installer (no --update flag) — it should auto-detect and update
    for script in ("install_windows.py", "install_linux.py"):
        result = _run_installer(script, target, "--enable", "none")
        assert result.returncode == 0, f"{script} failed: {result.stderr}"
        assert "summary" in result.stdout, f"{script} output missing summary: {result.stdout}"
