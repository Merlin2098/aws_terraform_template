from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


VERSION = "0.2.0"

DEFAULT_SCANNERS = ["python"]


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


@dataclass
class ScannerResult:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)


ScannerFn = Callable[[Path], ScannerResult]


def _iter_files(project_root: Path, pattern: str) -> list[Path]:
    from agents_framework.tools.inspect_project import is_ignored_path
    files: list[Path] = []
    for path in project_root.rglob(pattern):
        if is_ignored_path(path, project_root):
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


def scan_python(project_root: Path) -> ScannerResult:
    """Build Python module/import nodes and edges via the ``ast`` module."""
    files = _iter_files(project_root, "*.py")
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

    return ScannerResult(nodes=list(nodes.values()), edges=edges, issues=issues)


JS_EXTENSIONS = ("*.js", "*.jsx", "*.ts", "*.tsx")

JS_IMPORT_RE = re.compile(
    r"""(?:
        import\s+(?:[^'"]*?\sfrom\s+)?['"](?P<from>[^'"]+)['"]
        |
        require\(\s*['"](?P<require>[^'"]+)['"]\s*\)
    )""",
    re.VERBOSE,
)


def _js_module_name(project_root: Path, path: Path) -> str:
    rel = path.relative_to(project_root).as_posix()
    for suffix in (".tsx", ".ts", ".jsx", ".js"):
        if rel.endswith(suffix):
            rel = rel[: -len(suffix)]
            break
    if rel.endswith("/index"):
        rel = rel[: -len("/index")]
    return rel


def scan_javascript(project_root: Path) -> ScannerResult:
    """Build JS/TS module/import nodes and edges via regex-based import detection."""
    files: list[Path] = []
    for pattern in JS_EXTENSIONS:
        files.extend(_iter_files(project_root, pattern))

    module_to_file = {
        _js_module_name(project_root, path): path.relative_to(project_root).as_posix()
        for path in files
    }
    modules = set(module_to_file)
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for module, rel_path in module_to_file.items():
        nodes[f"module:{module}"] = Node(
            id=f"module:{module}",
            kind="javascript_module",
            label=module,
            module=module,
            file_path=rel_path,
        )

    for module, rel_path in module_to_file.items():
        path = project_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            issues.append({"file": rel_path, "message": str(exc)})
            continue

        source = f"module:{module}"
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in JS_IMPORT_RE.finditer(line):
                imported = match.group("from") or match.group("require")
                if not imported:
                    continue

                if imported.startswith("."):
                    base = (Path(rel_path).parent / imported).as_posix()
                    candidate = re.sub(r"/\./", "/", base)
                    while "/../" in candidate:
                        candidate = re.sub(r"[^/]+/\.\./", "", candidate, count=1)
                    candidate = candidate.lstrip("./")
                    internal = _pick_internal(candidate, modules) or _pick_internal(
                        f"{candidate}/index", modules
                    )
                    if internal:
                        target = f"module:{internal}"
                    else:
                        target = f"module:{candidate}"
                        nodes.setdefault(
                            target,
                            Node(id=target, kind="javascript_module", label=candidate),
                        )
                else:
                    package = imported.split("/")[0]
                    if package.startswith("@"):
                        parts = imported.split("/")
                        package = "/".join(parts[:2]) if len(parts) > 1 else package
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

    return ScannerResult(nodes=list(nodes.values()), edges=edges, issues=issues)


SCANNERS: dict[str, ScannerFn] = {
    "python": scan_python,
    "javascript": scan_javascript,
}


def active_scanners(project_root: Path) -> list[str]:
    from agents_framework.runtime.project_profile import resolve_project_profile
    resolved = resolve_project_profile(project_root, validate_dependencies=False)
    return list(resolved.scanners) or list(DEFAULT_SCANNERS)


def build_dependency_graph(
    project_root: Path, scanners: list[str] | None = None
) -> dict[str, Any]:
    project_root = project_root.resolve()
    scanner_names = scanners if scanners is not None else active_scanners(project_root)

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for name in scanner_names:
        scanner = SCANNERS.get(name)
        if scanner is None:
            continue
        result = scanner(project_root)
        for node in result.nodes:
            nodes.setdefault(node.id, node)
        edges.extend(result.edges)
        issues.extend(result.issues)

    internal_nodes = [node for node in nodes.values() if node.kind.endswith("_module")]
    external_nodes = [
        node for node in nodes.values() if node.kind == "external_package"
    ]

    return {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "scanners": scanner_names,
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


def build_and_persist_dependency_graph(
    project_root: Path, output_path: Path
) -> dict[str, Any]:
    graph = build_dependency_graph(project_root)
    write_dependency_graph(graph, output_path)
    return graph
