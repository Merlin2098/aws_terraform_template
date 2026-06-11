from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_installer(
    script: str, target: Path, *args: str
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
        check=False,
    )


def test_windows_installer_accepts_repeatable_capabilities(tmp_path: Path) -> None:
    target = tmp_path / "windows-host"

    result = _run_installer(
        "install_windows.py",
        target,
        "--cloud",
        "--enable",
        "business:saas",
        "--enable",
        "databases:supabase",
    )

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout
    assert not target.exists()


def test_linux_installer_accepts_local_shortcut(tmp_path: Path) -> None:
    target = tmp_path / "linux-host"

    result = _run_installer("install_linux.py", target, "--local")

    assert result.returncode == 0, result.stderr
    assert ".template-profile.yaml" in result.stdout
    assert "did not create or synchronize .venv" in result.stdout
    assert not target.exists()


def test_installers_reject_conflicting_environment_shortcuts(
    tmp_path: Path,
) -> None:
    result = _run_installer("install_linux.py", tmp_path / "host", "--local", "--cloud")

    assert result.returncode != 0
    assert "cannot be combined" in result.stderr
