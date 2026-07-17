from __future__ import annotations

from pathlib import Path

from agents_framework.runtime.dependency_graph import (
    active_scanners,
    build_dependency_graph,
    scan_javascript,
    scan_python,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_python_builds_internal_and_external_nodes(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "__init__.py", "")
    _write(tmp_path / "src" / "main.py", "import json\nfrom src.helpers import util\n")
    _write(tmp_path / "src" / "helpers.py", "import requests\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    result = scan_python(tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:src.main" in node_ids
    assert "module:src.helpers" in node_ids
    assert "external:json" in node_ids
    assert "external:requests" in node_ids

    edge_targets = {(edge.source, edge.target) for edge in result.edges}
    assert ("module:src.main", "module:src.helpers") in edge_targets
    assert ("module:src.main", "external:json") in edge_targets


def test_scan_javascript_resolves_relative_and_external_imports(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "App.tsx",
        "import React from 'react';\nimport { helper } from './helpers';\n",
    )
    _write(tmp_path / "src" / "helpers.ts", "export const helper = () => 1;\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    result = scan_javascript(tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:src/App" in node_ids
    assert "module:src/helpers" in node_ids
    assert "external:react" in node_ids

    edge_targets = {(edge.source, edge.target) for edge in result.edges}
    assert ("module:src/App", "module:src/helpers") in edge_targets
    assert ("module:src/App", "external:react") in edge_targets


def test_build_dependency_graph_with_explicit_scanners(tmp_path: Path) -> None:
    _write(tmp_path / "main.py", "import os\n")
    _write(tmp_path / "src" / "App.tsx", "import React from 'react';\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    graph = build_dependency_graph(tmp_path, scanners=["python", "javascript"])

    assert graph["scanners"] == ["python", "javascript"]
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "module:main" in node_ids
    assert "module:src/App" in node_ids
    assert "external:os" in node_ids
    assert "external:react" in node_ids


def test_active_scanners_falls_back_to_python_for_legacy_hosts(tmp_path: Path) -> None:
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    assert active_scanners(tmp_path) == ["python"]


def test_active_scanners_collects_from_active_capabilities(tmp_path: Path) -> None:
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )
    _write(
        tmp_path / "ai" / "capabilities" / "languages" / "python.yaml",
        "name: python\ntype: language\nscanners:\n  - python\n",
    )
    _write(
        tmp_path / "ai" / "capabilities" / "frameworks" / "react.yaml",
        "name: react\ntype: framework\nscanners:\n  - javascript\n",
    )
    _write(
        tmp_path / ".template-profile.yaml",
        "schema_version: 1\n"
        "capabilities:\n"
        "  languages:\n"
        "    python:\n"
        "      enabled: true\n"
        "  frameworks:\n"
        "    react:\n"
        "      enabled: true\n"
        "dependency_policy: {}\n",
    )

    assert active_scanners(tmp_path) == ["python", "javascript"]
