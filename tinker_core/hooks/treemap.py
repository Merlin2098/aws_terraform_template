from __future__ import annotations

from pathlib import Path


IGNORED_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tinker",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def _generate_tree(directory: Path, prefix: str = "") -> list[str]:
    try:
        items = sorted(
            directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())
        )
    except PermissionError:
        return []

    visible = [item for item in items if item.name not in IGNORED_NAMES]
    lines: list[str] = []

    for index, path in enumerate(visible):
        is_last = index == len(visible) - 1
        connector = "`-- " if is_last else "|-- "
        if path.is_dir():
            lines.append(f"{prefix}{connector}{path.name}/")
            child_prefix = f"{prefix}{'    ' if is_last else '|   '}"
            lines.extend(_generate_tree(path, child_prefix))
        else:
            lines.append(f"{prefix}{connector}{path.name}")

    return lines


def write_treemap(project_root: Path, output_file: Path) -> None:
    project_root = project_root.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "## Project Structure",
        "",
        "```text",
        f"{project_root.name}/",
        *_generate_tree(project_root),
        "```",
        "",
    ]
    output_file.write_text("\n".join(lines), encoding="utf-8")
