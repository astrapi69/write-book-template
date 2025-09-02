#!/usr/bin/env python3
# scripts/print_version_build.py
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Constants & Defaults
# ──────────────────────────────────────────────────────────────────────────────

# Allowed book types
VALID_BOOK_TYPES = ["paperback", "hardcover"]
DEFAULT_BOOK_TYPE = "paperback"

# Default scripts dir: project root / scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Public allow-lists (option *names* only, value-agnostic)
# Options that THIS script understands directly (not forwarded)
PRINT_VERSION_ALLOWED_OPTS = {
    "--book-type",
    "--export-format",
    "--scripts-dir",
    "--dry-run",
    "--no-restore",
    "--strict-opts",  # control abort-on-invalid behavior in this script
}

# Options that will be FORWARDED to full_export_book.py
# Keep this in sync with full_export_book.py CLI
FULL_EXPORT_ALLOWED_OPTS = {
    "--format",
    "--order",
    "--cover",
    "--epub2",
    "--lang",
    "--extension",
    "--book-type",
    "--output-file",
    "--skip-images",
    "--keep-relative-paths",
}

# ──────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────────────────────


def _split_valid_invalid_options(extra: List[str], allowed: set[str]) -> tuple[list[str], list[str]]:
    """
    Split passthrough args into (valid, invalid) based on *option names* only.
    Handles both '--opt=value' and '--opt value' forms. Non-option tokens are ignored.
    """
    valid: list[str] = []
    invalid: list[str] = []

    i = 0
    while i < len(extra):
        tok = extra[i]
        if tok.startswith("--"):
            name = tok.split("=", 1)[0]
            bucket = valid if name in allowed else invalid
            bucket.append(tok)
            # If value is in next token (e.g., --opt value) keep it with the same bucket
            if "=" not in tok and (i + 1) < len(extra) and not extra[i + 1].startswith("-"):
                bucket.append(extra[i + 1])
                i += 1
        # Bare tokens (positional) are ignored for this pipeline
        i += 1
    return valid, invalid


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
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}: {' '.join(cmd)}")
        return False


def git_restore_all(dry_run: bool = False) -> None:
    """
    Restore any working tree changes (used after a successful build).
    """
    cmd = ["git", "restore", "."]
    if dry_run:
        print(f"🔎 [dry-run] Would run: {' '.join(cmd)}")
        return
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ git restore failed (non-fatal). Exit code: {e.returncode}")


def build_steps(scripts_dir: Path, export_format: str, book_type: str) -> list[tuple[Path, list[str]]]:
    """
    Define the pipeline steps for building a print-optimized EPUB.

    Currently a single step that calls full_export_book.py with format 'epub'.
    Adjust this if your real pipeline has multiple pre/post steps.
    """
    steps: list[tuple[Path, list[str]]] = []

    full_export = scripts_dir / "full_export_book.py"

    # Always export EPUB for print-version (you can still override via forwarded extras)
    base_args: list[str] = [
        "--format",
        export_format,
        "--book-type",
        book_type,
        "--output-file",
        "print-version",  # logical basename; underlying script may append extension
    ]

    steps.append((full_export, base_args))
    return steps


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build a print-ready version of the book (EPUB export pipeline)."
    )

    p.add_argument(
        "--book-type",
        default=DEFAULT_BOOK_TYPE,
        help=f"Book type to build ({', '.join(VALID_BOOK_TYPES)}). Default: {DEFAULT_BOOK_TYPE}",
    )
    p.add_argument(
        "--export-format",
        default="epub",
        choices=["epub"],  # print-version target is EPUB; keep choices if you expand later
        help="Output format for print version (currently only 'epub').",
    )
    p.add_argument(
        "--scripts-dir",
        type=Path,
        default=DEFAULT_SCRIPTS_DIR,
        help=f"Directory where pipeline scripts reside. Default: {DEFAULT_SCRIPTS_DIR}",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    p.add_argument(
        "--no-restore",
        action="store_true",
        help="Skip 'git restore .' at the end on success.",
    )

    # We accept unknowns so we can validate/forward to full_export_book.py
    args, extra = p.parse_known_args(list(argv) if argv is not None else None)
    args._extra = extra  # stash passthrough

    # Lightweight strict mode via presence of --strict-opts (not forwarded)
    args.strict_opts = any(t == "--strict-opts" for t in extra)
    args._extra = [t for t in args._extra if t != "--strict-opts"]

    # Validate book type with fallback
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


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)

    print(f"📘 Building PRINT version of the book ({args.book_type.upper()})...\n")

    # Validate and split extras for the full_export step
    valid_extra, invalid_extra = _split_valid_invalid_options(
        getattr(args, "_extra", []),
        FULL_EXPORT_ALLOWED_OPTS,
    )

    if invalid_extra:
        print("⚠️ Detected invalid options for full_export_book.py:")
        for tok in invalid_extra:
            print(f"   - {tok}")
        if args.strict_opts:
            print("🛑 Aborting due to --strict-opts.")
            sys.exit(2)

    if valid_extra:
        print("🔧 Forwarding valid options to full_export_book.py:")
        print("   " + " ".join(valid_extra))

    steps = build_steps(args.scripts_dir, args.export_format, args.book_type)

    for script_path, arguments in steps:
        # Inject filtered extras only for the full_export step
        if script_path.name == "full_export_book.py" and valid_extra:
            merged = [*arguments, *valid_extra]
            ok = run_script(script_path, *merged, dry_run=args.dry_run)
        else:
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
