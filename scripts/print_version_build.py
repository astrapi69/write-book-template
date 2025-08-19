#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Iterable, List, Tuple

# Allowed book types
VALID_BOOK_TYPES = ["paperback", "hardcover"]
DEFAULT_BOOK_TYPE = "paperback"

# Default scripts dir: project root / scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def run_script(script_path: Path, *args: str, dry_run: bool = False) -> bool:
    """
    Run a Python script located at 'script_path' with the provided args.
    Returns True when command completes (or in dry-run), False on error/missing.
    """
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    cmd: List[str] = [sys.executable, str(script_path), *args]

    if dry_run:
        print(f"🔎 [dry-run] Would run: {' '.join(cmd)}")
        return True

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Ran: {script_path.name} {' '.join(args) if args else ''}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_path.name}: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Failed to execute interpreter or script: {e}")
        return False


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a print-ready version of the book (EPUB export pipeline)."
    )
    p.add_argument(
        "--book-type",
        default=DEFAULT_BOOK_TYPE,
        help=f"Specify the book type (default: {DEFAULT_BOOK_TYPE}; allowed: {', '.join(VALID_BOOK_TYPES)})",
    )
    p.add_argument(
        "--export-format",
        default="epub",
        help="Export format passed to full_export_book.py (default: epub)",
    )
    p.add_argument(
        "--scripts-dir",
        type=Path,
        default=DEFAULT_SCRIPTS_DIR,
        help="Directory containing pipeline scripts (default: ./scripts relative to repo root).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the commands that would run, without executing.",
    )
    p.add_argument(
        "--no-restore",
        action="store_true",
        help="Skip 'git restore .' at the end on success.",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    # Validate book type manually to preserve original behavior (fallback)
    bt = (args.book_type or "").lower()
    if bt not in VALID_BOOK_TYPES:
        print(
            f"⚠️ Invalid book type '{args.book_type}' provided. "
            f"Falling back to default: '{DEFAULT_BOOK_TYPE}'"
        )
        args.book_type = DEFAULT_BOOK_TYPE
    else:
        args.book_type = bt

    return args


def build_steps(scripts_dir: Path, export_format: str, book_type: str) -> List[Tuple[Path, List[str]]]:
    """
    Returns the pipeline steps as (script_path, [args...]).
    """
    return [
        (scripts_dir / "strip_links.py", []),
        (scripts_dir / "convert_links_to_plain_text.py", []),
        (
            scripts_dir / "full_export_book.py",
            [f"--format={export_format}", f"--book-type={book_type}"],
        ),
    ]


def git_restore_all(dry_run: bool = False) -> bool:
    cmd = ["git", "restore", "."]
    if dry_run:
        print(f"🔎 [dry-run] Would run: {' '.join(cmd)}")
        return True
    try:
        subprocess.run(cmd, check=True)
        print("✅ Reverted all changes using git restore")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to revert changes: {e}")
        return False


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)

    print(f"📘 Building PRINT version of the book ({args.book_type.upper()})...\n")

    steps = build_steps(args.scripts_dir, args.export_format, args.book_type)

    for script_path, arguments in steps:
        ok = run_script(script_path, *arguments, dry_run=args.dry_run)
        if not ok:
            print("🛑 Build process aborted.")
            sys.exit(1)

    print("\n🎉 Print version EPUB successfully generated!")
    if not args.no_restore:
        print("\n🔄 Reverting modified files to original state...")
        git_restore_all(dry_run=args.dry_run)

    sys.exit(0)


if __name__ == "__main__":
    main()
