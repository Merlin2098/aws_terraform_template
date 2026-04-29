#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from ai.installer import install_template, print_summary


def _prompt_target() -> Path:
    selected = input("Destination repository directory (absolute path): ").strip()
    if not selected:
        raise ValueError("No target folder selected.")
    target = Path(selected).expanduser()
    if not target.is_absolute():
        raise ValueError(
            "Target must be an absolute path, for example /home/user/project."
        )
    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install this AWS Terraform template into another repository."
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Absolute destination repository directory. If omitted, a CLI prompt is used.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing target files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the files that would be copied without writing anything.",
    )
    args = parser.parse_args()

    try:
        if args.target is not None:
            target = args.target.expanduser()
            if not target.is_absolute():
                raise ValueError(
                    "Target must be an absolute path, for example /home/user/project."
                )
        else:
            target = _prompt_target()

        summary = install_template(
            target=target,
            force=args.force,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        parser.error(str(exc))

    print_summary(summary, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
