from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ai.installer import STATE_FILENAME, install_template


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = "install.py"


def _run_installer(
    target: Path, *args: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            INSTALLER,
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


def _run_update(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            INSTALLER,
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


def test_installer_accepts_repeatable_capabilities(tmp_path: Path) -> None:
    target = tmp_path / "host"

    result = _run_installer(
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


def test_installer_accepts_none_selection(tmp_path: Path) -> None:
    target = tmp_path / "host"

    result = _run_installer(target, "--enable", "none")

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout
    assert not target.exists()


def test_empty_interactive_selection_enables_all_capabilities(tmp_path: Path) -> None:
    result = _run_installer(
        tmp_path / "host",
        input_text="\n",
    )

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout


def test_installer_rejects_removed_environment_shortcuts(tmp_path: Path) -> None:
    result = _run_installer(tmp_path / "host", "--local")

    assert result.returncode != 0
    assert "unrecognized arguments: --local" in result.stderr


def test_installer_update_on_installed_host_succeeds(tmp_path: Path) -> None:
    target = tmp_path / "update-host"
    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        enabled_capabilities=["none"],
    )
    assert (target / STATE_FILENAME).exists()

    result = _run_update(target)

    assert result.returncode == 0, result.stderr
    assert "summary" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout


def test_update_without_prior_install_exits_with_error(tmp_path: Path) -> None:
    target = tmp_path / "no-state-host"
    target.mkdir()

    result = _run_update(target)
    assert result.returncode != 0, "installer should fail without prior install"
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
    result = _run_installer(target, "--enable", "none")
    assert result.returncode == 0, f"installer failed: {result.stderr}"
    assert "summary" in result.stdout, f"installer output missing summary: {result.stdout}"
