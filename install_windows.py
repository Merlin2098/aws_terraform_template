from __future__ import annotations

import argparse
from pathlib import Path

from ai.installer import (
    install_template,
    print_summary,
    prompt_environment_profile,
    prompt_include_structure,
    select_target_folder,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install this AWS Terraform template into another repository."
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Destination repository directory. If omitted, a folder picker opens.",
    )
    parser.add_argument(
        "--select-target",
        action="store_true",
        help="Open a folder picker to select the destination repository directory.",
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
    parser.add_argument(
        "--with-structure",
        action="store_true",
        help="Copy the optional src/, infra/, and tests/ trees without prompting.",
    )
    parser.add_argument(
        "--without-structure",
        action="store_true",
        help="Skip the optional src/, infra/, and tests/ trees without prompting.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Install template dependencies for a local-only host project.",
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Install template dependencies for a cloud host project.",
    )
    args = parser.parse_args()

    if args.with_structure and args.without_structure:
        parser.error("--with-structure cannot be combined with --without-structure.")
    if args.local and args.cloud:
        parser.error("--local cannot be combined with --cloud.")

    try:
        target = (
            select_target_folder()
            if args.select_target or not args.target
            else args.target
        )
        include_structure = (
            True
            if args.with_structure
            else False
            if args.without_structure
            else prompt_include_structure()
        )
        environment_profile = (
            "local"
            if args.local
            else "cloud"
            if args.cloud
            else prompt_environment_profile()
        )
        summary = install_template(
            target=target,
            force=args.force,
            dry_run=args.dry_run,
            include_structure=include_structure,
            environment_profile=environment_profile,
        )
    except ValueError as exc:
        parser.error(str(exc))

    print_summary(summary, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
