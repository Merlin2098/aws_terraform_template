from __future__ import annotations

from pathlib import Path

import pytest

from ai.runtime.profile import DependencyPolicy, Profile
from ai.runtime.project_profile import resolve_project_profile, uv_sync_args


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _project(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        """
[project]
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
    descriptors = {
        "languages/python.yaml": """
name: python
dependencies:
  extras: [local]
  groups: [dev-local]
scanners: [python]
""",
        "cloud/aws.yaml": """
name: aws
depends_on:
  languages: [python]
dependencies:
  extras: [cloud]
  groups: [dev-cloud]
""",
        "infrastructure/terraform.yaml": """
name: terraform
depends_on:
  cloud: [aws]
""",
        "frameworks/react.yaml": """
name: react
depends_on:
  languages: [python]
scanners: [javascript]
""",
        "business/saas.yaml": """
name: saas
depends_on:
  frameworks: [react]
  languages: [python]
dependencies:
  extras: [saas]
""",
        "databases/supabase.yaml": """
name: supabase
depends_on:
  business: [saas]
dependencies:
  extras: [supabase]
""",
    }
    for relative, content in descriptors.items():
        _write(tmp_path / "ai" / "capabilities" / relative, content)


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
    _write(
        tmp_path / "ai/capabilities/cloud/aws.yaml",
        "name: aws\ndepends_on:\n  infrastructure: [terraform]\n",
    )

    with pytest.raises(ValueError, match="cycle"):
        resolve_project_profile(
            tmp_path,
            profile=Profile(capabilities={"infrastructure": ["terraform"]}),
        )


def test_missing_pyproject_extra_is_rejected(tmp_path: Path) -> None:
    _project(tmp_path)
    _write(
        tmp_path / "ai/capabilities/cloud/aws.yaml",
        "name: aws\ndependencies:\n  extras: [missing]\n",
    )

    with pytest.raises(ValueError, match="unknown pyproject extras"):
        resolve_project_profile(
            tmp_path, profile=Profile(capabilities={"cloud": ["aws"]})
        )
