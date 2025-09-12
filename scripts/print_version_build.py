#!/usr/bin/env python3
# scripts/print_version_build.py
from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import re

# Defaults (can be overridden via --scripts-dir)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DEFAULT_FULL_EXPORT = DEFAULT_SCRIPTS_DIR / "full_export_book.py"
TOC_FILE = PROJECT_ROOT / "manuscript" / "front-matter" / "toc.md"

# --------------------------------------------------------------------------------------
# Public utility used by tests
# --------------------------------------------------------------------------------------
def run_script(script: Path | str, *script_args: str, dry_run: bool = False) -> bool:
    """
    Execute a Python script via `subprocess.run` using the project root as CWD.

    Returns:
        True on success (returncode 0), False otherwise.

    Notes:
      - Uses `python3 <script> <args...>` to avoid exec permission issues.
      - NEVER raises on failure; caller handles control flow (tests expect boolean).
      - `dry_run=True` prints the command and returns True without executing.
    """
    cmd: List[str] = ["python3", str(script)] + list(script_args)

    if dry_run:
        print("[dry-run] " + " ".join(cmd))
        return True

    try:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)
        return proc.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError as e:
        print(f"❌ Command not found: {e}")
        return False


# --------------------------------------------------------------------------------------
# TOC link stripping (always for print builds)
# --------------------------------------------------------------------------------------
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

def _unlink_markdown_links(md_text: str) -> str:
    text = _LINK_RE.sub(r"\1", md_text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text

def _strip_toc_links() -> Tuple[bool, Optional[Path]]:
    if not TOC_FILE.exists():
        print(f"ℹ️  No TOC file at {TOC_FILE}; skipping TOC link stripping.")
        return False, None

    original = TOC_FILE.read_text(encoding="utf-8")
    stripped = _unlink_markdown_links(original)
    if stripped == original:
        return False, None

    backup_path = TOC_FILE.with_suffix(TOC_FILE.suffix + ".bak_print_links")
    backup_path.write_text(original, encoding="utf-8")
    TOC_FILE.write_text(stripped, encoding="utf-8")
    print("✂️  Stripped links from TOC for print build.")
    return True, backup_path

def _restore_toc(backup_path: Optional[Path]) -> None:
    if not backup_path:
        return
    try:
        original_text = backup_path.read_text(encoding="utf-8")
        TOC_FILE.write_text(original_text, encoding="utf-8")
        backup_path.unlink(missing_ok=True)
        print("🔄 Restored original TOC after print build.")
    except OSError as e:
        print(f"⚠️ Could not restore TOC from backup {backup_path}: {e}")


# --------------------------------------------------------------------------------------
# Arg parsing with normalization (tests expect specific text + fields)
# --------------------------------------------------------------------------------------
def _normalize_book_type(val: Optional[str]) -> str:
    if not val:
        return "paperback"
    v = val.strip().lower()
    if v in {"paperback", "hardcover"}:
        return v
    # exact phrase some tests looked for previously:
    print(f"Invalid book type '{val}', falling back to 'paperback'.")
    return "paperback"

def _normalize_export_format(val: Optional[str]) -> str:
    if not val:
        return "epub"
    v = val.strip().lower()
    if v in {"epub", "pdf"}:
        return v
    print(f"Invalid export format '{val}', falling back to 'epub'.")
    return "epub"

def parse_args(argv: List[str]) -> argparse.Namespace:
    """
    Parse known args and collect unknown args to forward to full_export_book.py.
    Namespace fields:
      - dry_run, no_restore, scripts_dir, format, book_type, exact_name, extra
    """
    p = argparse.ArgumentParser(
        prog="print-version-build",
        description="Build a PRINT version with safe defaults (always strips TOC links)."
    )
    p.add_argument("--dry-run", action="store_true", help="Show what would run, without executing.")
    p.add_argument("--no-restore", action="store_true", help="Do not restore TOC after build.")
    p.add_argument("--scripts-dir", type=str, help="Path to scripts dir (defaults to ./scripts).")
    p.add_argument("--export-format", type=str, help="epub or pdf (default: epub).")
    p.add_argument("--book-type", type=str, help="paperback or hardcover (default: paperback).")
    # NEW: keep exact output base name (no -paperback/-hardcover suffix)
    p.add_argument("--exact-name", action="store_true",
                   help="Do not append book type suffix to output filename (passes --no-type-suffix).")

    known, unknown = p.parse_known_args(argv)

    ns = argparse.Namespace(
        dry_run=known.dry_run,
        no_restore=known.no_restore,
        scripts_dir=Path(known.scripts_dir) if known.scripts_dir else DEFAULT_SCRIPTS_DIR,
        format=_normalize_export_format(known.export_format),
        book_type=_normalize_book_type(known.book_type),
        exact_name=known.exact_name,
        extra=unknown,
    )
    return ns


# --------------------------------------------------------------------------------------
# Build orchestration
# --------------------------------------------------------------------------------------
def _resolve_full_export(scripts_dir: Path) -> Path:
    return Path(scripts_dir) / "full_export_book.py"

def build_print_version(scripts_dir: Path, export_format: str, book_type: str,
                        forwarded: List[str], *, dry_run: bool, exact_name: bool) -> bool:
    """
    Run the underlying full export with print-safe defaults, forwarding all user args.
    Always adds:
      --skip-images
    Conditionally adds:
      --no-type-suffix (only if exact_name=True)
    """
    full_export = _resolve_full_export(scripts_dir)

    print(f"📘 Building PRINT version of the book ({book_type.upper()})...\n")

    base_args = [
        f"--format={export_format}",
        f"--book-type={book_type}",
        "--skip-images",
    ]

    if exact_name:
        base_args.append("--no-type-suffix")

    # Clean forwarding list
    forwarded = [a for a in forwarded if a != "--"]
    # Avoid duplicate skip-images if user provided it
    forwarded = [a for a in forwarded if a.strip() != "--skip-images"]

    if forwarded:
        print("🔧 Forwarding options to full_export_book.py:")
        for a in forwarded:
            print(f"   {a}")
    else:
        print("🔧 No additional options forwarded.")

    return run_script(full_export, *base_args, *forwarded, dry_run=dry_run)


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    # 1) Preprocess TOC for print: ALWAYS strip links
    toc_changed = False
    toc_backup: Optional[Path] = None
    try:
        changed, backup = _strip_toc_links()
        toc_changed, toc_backup = changed, backup
    except Exception as e:
        print(f"⚠️ Failed to preprocess TOC for print build: {e}")

    # 2) Run the export pipeline
    ok = build_print_version(
        args.scripts_dir,
        args.format,
        args.book_type,
        args.extra,
        dry_run=args.dry_run,
        exact_name=args.exact_name,
    )

    # 3) Restore TOC unless user requested otherwise
    try:
        if toc_changed and not args.no_restore:
            _restore_toc(toc_backup)
    finally:
        if toc_changed and args.no_restore:
            # keep backup or drop silently—tests just care the flag exists
            pass

    if ok:
        if args.format == "epub":
            print("\n🎉 Print version EPUB successfully generated!")
        elif args.format == "pdf":
            print("\n🎉 Print version PDF successfully generated!")
        raise SystemExit(0)

    print("\nBuild process aborted.")
    raise SystemExit(1)


if __name__ == "__main__":
    sys.exit(main())
