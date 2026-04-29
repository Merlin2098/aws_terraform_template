from __future__ import annotations

from pathlib import Path

from ai.runtime.config import load_context_config


def _generate_tree(
    directory: Path, ignored_names: set[str], prefix: str = ""
) -> list[str]:
    try:
        items = sorted(
            directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())
        )
    except PermissionError:
        return []

    visible = [item for item in items if item.name not in ignored_names]
    lines: list[str] = []

    for index, path in enumerate(visible):
        is_last = index == len(visible) - 1
        connector = "`-- " if is_last else "|-- "
        if path.is_dir():
            lines.append(f"{prefix}{connector}{path.name}/")
            child_prefix = f"{prefix}{'    ' if is_last else '|   '}"
            lines.extend(_generate_tree(path, ignored_names, child_prefix))
        else:
            lines.append(f"{prefix}{connector}{path.name}")

    return lines


def write_treemap(project_root: Path, output_file: Path) -> None:
    project_root = project_root.resolve()
    config = load_context_config(project_root)
    ignored_names = set(config.get("treemap_ignore_dirs", []))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "## Project Structure",
        "",
        "```text",
        f"{project_root.name}/",
        *_generate_tree(project_root, ignored_names),
        "```",
        "",
    ]
    output_file.write_text("\n".join(lines), encoding="utf-8")
