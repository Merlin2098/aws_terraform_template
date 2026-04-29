from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinker_core.tools.inspect_project import IGNORED_DIRS


VERSION = "0.1.0"


@dataclass
class Node:
    id: str
    kind: str
    label: str
    module: str | None = None
    file_path: str | None = None


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    raw: str
    lineno: int | None = None


def _iter_python_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in project_root.rglob("*.py"):
        rel = path.relative_to(project_root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] == "ai":
            continue
        if any(part.startswith(".") and part not in {".github"} for part in rel.parts):
            continue
        files.append(path)
    return files


def _module_name(project_root: Path, path: Path) -> str:
    rel = path.relative_to(project_root).as_posix()
    if rel == "main.py":
        return "main"
    if rel.endswith("/__init__.py"):
        return rel[: -len("/__init__.py")].replace("/", ".")
    if rel == "__init__.py":
        return "__init__"
    return rel[:-3].replace("/", ".")


def _pick_internal(imported: str, modules: set[str]) -> str | None:
    if imported in modules:
        return imported
    parts = imported.split(".")
    for index in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:index])
        if candidate in modules:
            return candidate
    return None


def build_dependency_graph(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    files = _iter_python_files(project_root)
    module_to_file = {
        _module_name(project_root, path): path.relative_to(project_root).as_posix()
        for path in files
    }
    modules = set(module_to_file)
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for module, rel_path in module_to_file.items():
        nodes[f"module:{module}"] = Node(
            id=f"module:{module}",
            kind="python_module",
            label=module,
            module=module,
            file_path=rel_path,
        )

    for module, rel_path in module_to_file.items():
        path = project_root / rel_path
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        except Exception as exc:
            issues.append({"file": rel_path, "message": str(exc)})
            continue

        source = f"module:{module}"
        for node in ast.walk(tree):
            imports: list[tuple[str, int | None]] = []
            if isinstance(node, ast.Import):
                imports = [
                    (alias.name, getattr(node, "lineno", None)) for alias in node.names
                ]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports = [(node.module, getattr(node, "lineno", None))]

            for imported, lineno in imports:
                internal = _pick_internal(imported, modules)
                if internal:
                    target = f"module:{internal}"
                else:
                    package = imported.split(".")[0]
                    target = f"external:{package}"
                    nodes.setdefault(
                        target,
                        Node(
                            id=target,
                            kind="external_package",
                            label=package,
                            module=package,
                        ),
                    )
                edges.append(
                    Edge(
                        source=source,
                        target=target,
                        kind="imports",
                        raw=imported,
                        lineno=lineno,
                    )
                )

    internal_nodes = [node for node in nodes.values() if node.kind == "python_module"]
    external_nodes = [
        node for node in nodes.values() if node.kind == "external_package"
    ]

    return {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "nodes": [
            asdict(node) for node in sorted(nodes.values(), key=lambda item: item.id)
        ],
        "edges": [asdict(edge) for edge in edges],
        "issues": issues,
        "summary": {
            "internal_modules": len(internal_nodes),
            "external_packages": len(external_nodes),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "issues": len(issues),
        },
    }


def write_dependency_graph(graph: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_and_persist_dependency_graph(project_root: Path) -> dict[str, Any]:
    graph = build_dependency_graph(project_root)
    write_dependency_graph(graph, project_root / ".tinker" / "dependencies_graph.json")
    return graph
