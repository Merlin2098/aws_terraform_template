from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agents_framework.runtime.capability_registry import CapabilityDescriptor
from agents_framework.runtime.profile import DependencyPolicy, Profile
from agents_framework.runtime.project_profile import resolve_project_profile, uv_sync_args


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _project(tmp_path: Path) -> None:
    """Write a minimal pyproject.toml with extras matching real framework capabilities."""
    _write(
        tmp_path / "pyproject.toml",
        """[project]
name = "sample"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
local = []
cloud = []
saas = []
supabase = []

[dependency-groups]
dev-local = []
dev-cloud = []
""",
    )


def test_resolves_transitive_terraform_dependencies(tmp_path: Path) -> None:
    _project(tmp_path)
    profile = Profile(capabilities={"infrastructure": ["terraform"]})

    resolved = resolve_project_profile(tmp_path, profile=profile)

    assert resolved.explicit_capabilities == ("infrastructure:terraform",)
    assert resolved.implicit_capabilities == ("languages:python", "cloud:aws")
    assert resolved.extras == ("local", "cloud")
    assert resolved.groups == ("dev-local", "dev-cloud")


def test_resolves_supabase_dependency_chain(tmp_path: Path) -> None:
    _project(tmp_path)
    profile = Profile(capabilities={"databases": ["supabase"]})

    resolved = resolve_project_profile(tmp_path, profile=profile)

    assert resolved.extras == ("local", "saas", "supabase")
    assert set(resolved.implicit_capabilities) == {
        "languages:python",
        "frameworks:react",
        "business:saas",
    }


def test_no_dev_omits_groups(tmp_path: Path) -> None:
    _project(tmp_path)
    profile = Profile(
        capabilities={"cloud": ["aws"]},
        dependency_policy=DependencyPolicy(include_dev=False),
    )

    resolved = resolve_project_profile(tmp_path, profile=profile)

    assert resolved.groups == ()
    assert uv_sync_args(resolved) == [
        "sync",
        "--no-default-groups",
        "--extra",
        "local",
        "--extra",
        "cloud",
    ]
    assert "--locked" in uv_sync_args(resolved, locked=True)


def test_unknown_capability_is_rejected(tmp_path: Path) -> None:
    _project(tmp_path)

    with pytest.raises(ValueError, match="Unknown capability"):
        resolve_project_profile(
            tmp_path, profile=Profile(capabilities={"cloud": ["azure"]})
        )


def test_unknown_disabled_capability_is_rejected(tmp_path: Path) -> None:
    _project(tmp_path)

    with pytest.raises(ValueError, match="Unknown capability"):
        resolve_project_profile(
            tmp_path,
            profile=Profile(
                capabilities={},
                declared_capabilities={"cloud": ["azure"]},
            ),
        )


def test_cycle_is_rejected(tmp_path: Path) -> None:
    _project(tmp_path)

    _empty = {
        cat: {}
        for cat in ["languages", "frameworks", "databases", "ai", "platform", "business", "operations"]
    }
    cycle_registry = {
        **_empty,
        "cloud": {
            "aws": CapabilityDescriptor(
                name="aws",
                category="cloud",
                depends_on={"infrastructure": ["terraform"]},
            )
        },
        "infrastructure": {
            "terraform": CapabilityDescriptor(
                name="terraform",
                category="infrastructure",
                depends_on={"cloud": ["aws"]},
            )
        },
    }

    with patch("agents_framework.runtime.project_profile.load_registry", return_value=cycle_registry):
        with pytest.raises(ValueError, match="cycle"):
            resolve_project_profile(
                tmp_path,
                profile=Profile(capabilities={"infrastructure": ["terraform"]}),
            )


def test_missing_pyproject_extra_is_rejected(tmp_path: Path) -> None:
    # pyproject.toml declares only "other", not the extras needed by cloud:aws
    _write(
        tmp_path / "pyproject.toml",
        """[project]
name = "sample"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
other = []
""",
    )

    with pytest.raises(ValueError, match="unknown pyproject extras"):
        resolve_project_profile(
            tmp_path, profile=Profile(capabilities={"cloud": ["aws"]})
        )
