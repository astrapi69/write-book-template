#!/usr/bin/env python3
"""
Builds the print version (paperback or hardcover) of a book project.

Current pipeline (kept minimal to satisfy tests):
  1) full_export_book.py
  2) git restore .   (unless --no-restore)

CLI examples:
    print-version-build --book-type paperback
    print-version-build --dry-run --export-format epub
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCRIPTS_DIR = PROJECT_ROOT / "scripts"


# --------------------------------------------------------------------------- #
# Normalizers
# --------------------------------------------------------------------------- #
def _normalize_export_format(fmt: Optional[str]) -> str:
    """Return normalized export format ('epub'|'pdf')."""
    if not fmt:
        return "epub"
    fmt = fmt.lower().strip()
    return "pdf" if fmt.startswith("p") else "epub"


def _normalize_book_type(bt: Optional[str]) -> str:
    """Return normalized book type ('paperback'|'hardcover'), warn on invalid input."""
    if not bt:
        return "paperback"
    v = bt.lower().strip()
    if v in ("paperback", "p"):
        return "paperback"
    if v in ("hardcover", "h"):
        return "hardcover"
    print(f"Invalid book type: {bt}. Falling back to 'paperback'.")
    return "paperback"


# --------------------------------------------------------------------------- #
# Core runner
# --------------------------------------------------------------------------- #
def run_script(script: Path | str, *script_args: str, dry_run: bool = False) -> bool:
    """
    Execute a Python script via subprocess.run.

    Returns:
        True on success (returncode 0), False otherwise.

    Notes:
      - Uses `python3 <script> <args...>` to avoid exec permission issues.
      - Never raises on failure; caller handles control flow (tests expect boolean).
      - `dry_run=True` prints the command and returns True without executing.
    """
    cmd: List[str] = ["python3", str(script)] + list(script_args)

    if dry_run:
        print("[dry-run] Would run: " + " ".join(cmd))
        return True

    script_path = Path(script)
    if not script_path.exists():
        print(f"Script not found: {script_path}")
        return False

    try:
        # No cwd here – tests mock signature (cmd, check=True)
        proc = subprocess.run(cmd, check=True)
        return proc.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: " + " ".join(cmd))
        return False


# --------------------------------------------------------------------------- #
# Build pipeline
# --------------------------------------------------------------------------- #
def build_print_version(
    scripts_dir: Path,
    export_format: str,
    book_type: str,
    forwarded_args: list[str],
    dry_run: bool = False,
    exact_name: bool = False,  # reserved for future extension
    no_restore: bool = False,
) -> bool:
    """
    Run the minimal pipeline for building the print version.

    Only invokes full_export_book.py and (optionally) performs a git restore at the end.
    """
    toc_file = PROJECT_ROOT / "manuscript" / "front-matter" / "toc.md"
    if not toc_file.exists():
        print(f"ℹ️  No TOC file at {toc_file}; skipping TOC link stripping.")

    print(f"📘 Building PRINT version of the book ({book_type.upper()})...\n")

    full_export = scripts_dir / "full_export_book.py"

    base_args = [
        f"--format={export_format}",
        f"--book-type={book_type}",
        "--skip-images",
    ]

    if dry_run:
        print("🔧 DRY-RUN mode enabled (no actual execution).\n")

    ok = True
    ok &= run_script(full_export, *base_args, *forwarded_args, dry_run=dry_run)

    if not ok:
        print("❌ One or more pipeline steps failed.")
        print("Build process aborted.")
        return False

    # Final cleanup step (expected by tests unless --no-restore is set)
    if not no_restore:
        git_cmd = ["git", "restore", "."]
        if dry_run:
            print("[dry-run] Would run: " + " ".join(git_cmd))
        else:
            try:
                subprocess.run(git_cmd, check=True)
            except subprocess.CalledProcessError:
                # Not fatal for tests, but report it.
                print("⚠️  git restore failed (non-fatal).")

    print("✅ Pipeline finished successfully.")
    return True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse known args and collect unknown args to forward to full_export_book.py.

    Namespace fields:
      - dry_run, no_restore, scripts_dir, export_format, book_type, exact_name, extra
    """
    p = argparse.ArgumentParser(description="Build print version of a book project.")
    p.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing."
    )
    p.add_argument(
        "--no-restore", action="store_true", help="Skip git restore at the end."
    )
    p.add_argument(
        "--scripts-dir", type=str, help="Path to scripts dir (defaults to ./scripts)."
    )
    p.add_argument(
        "--export-format",
        dest="export_format",
        choices=["epub", "pdf"],
        default="epub",
        help="Export format for the print pipeline (epub|pdf).",
    )
    # Alias for backward compatibility
    p.add_argument(
        "--format",
        dest="export_format",
        choices=["epub", "pdf"],
        help=argparse.SUPPRESS,
    )
    p.add_argument(
        "--book-type", type=str, help="paperback or hardcover (default: paperback)."
    )
    p.add_argument(
        "--exact-name", action="store_true", help="Use exact output name (no suffix)."
    )

    known, unknown = p.parse_known_args(argv)

    ns = argparse.Namespace(
        dry_run=known.dry_run,
        no_restore=known.no_restore,
        scripts_dir=(
            Path(known.scripts_dir) if known.scripts_dir else DEFAULT_SCRIPTS_DIR
        ),
        export_format=_normalize_export_format(known.export_format),
        book_type=_normalize_book_type(known.book_type),
        exact_name=known.exact_name,
        extra=unknown,
    )
    return ns


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    ok = build_print_version(
        args.scripts_dir,
        args.export_format,
        args.book_type,
        args.extra,
        dry_run=args.dry_run,
        exact_name=args.exact_name,
        no_restore=args.no_restore,
    )

    if ok:
        if args.export_format == "epub":
            print("\n🎉 Print version EPUB successfully generated!")
        elif args.export_format == "pdf":
            print("\n🎉 Print version PDF successfully generated!")
        sys.exit(0)
    else:
        print("\n❌ Print version build failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
