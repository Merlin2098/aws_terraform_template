from __future__ import annotations

from pathlib import Path

from ai.installer import install_template


def test_local_install_copies_only_local_and_dev_requirements(tmp_path: Path) -> None:
    target = tmp_path / "host-local"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
    )

    assert "requirements.local.txt" in summary["copied"]
    assert "requirements.dev.txt" in summary["copied"]
    assert "requirements.cloud.txt" not in summary["copied"]
    assert not (target / "requirements.txt").exists()
    assert (target / "requirements.local.txt").exists()
    assert (target / "requirements.dev.txt").exists()
    assert not (target / "requirements.cloud.txt").exists()


def test_cloud_install_copies_cloud_requirements(tmp_path: Path) -> None:
    target = tmp_path / "host-cloud"

    summary = install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="cloud",
    )

    assert "requirements.local.txt" in summary["copied"]
    assert "requirements.dev.txt" in summary["copied"]
    assert "requirements.cloud.txt" in summary["copied"]
    assert not (target / "requirements.txt").exists()
    assert (target / "requirements.cloud.txt").exists()


def test_existing_host_requirements_txt_is_left_untouched(tmp_path: Path) -> None:
    target = tmp_path / "host-existing"
    target.mkdir(parents=True)
    requirements_txt = target / "requirements.txt"
    original = "custom-package==1.0.0\n"
    requirements_txt.write_text(original, encoding="utf-8")

    install_template(
        target=target,
        force=False,
        dry_run=False,
        include_structure=False,
        environment_profile="local",
    )

    assert requirements_txt.read_text(encoding="utf-8") == original
