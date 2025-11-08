#!/usr/bin/env python3
# unbold_md_headers.py
"""
Removes bold Markdown markers (**...**) that appear directly inside header lines.
Example:
    "### **From Paper to Practice**"  →  "### From Paper to Practice"
    "### **Title** with subtitle"    →  "### Title with subtitle"

Default behavior:
- Processes all .md files (recursively)
- Creates .bak backups
- Works safely in-place
"""

from __future__ import annotations
import argparse
import re
from pathlib import Path
import sys
from typing import Iterable, Sequence, Set

# Match Markdown headers that contain **...** after the # prefix
PATTERN = re.compile(r"^(\s*#{1,6}\s+)\*\*(.+?)\*\*(\s*.*)$")


def levels_filter(line: str, allowed: set[int] | None) -> bool:
    """Return True if the line is a Markdown header (and within allowed levels, if specified)."""
    if not line.lstrip().startswith("#"):
        return False
    hashes = 0
    for ch in line.lstrip():
        if ch == "#":
            hashes += 1
        else:
            break
    return allowed is None or hashes in allowed


# add this helper (optional but clean)
def _split_eol(s: str) -> tuple[str, str]:
    if s.endswith("\r\n"):
        return s[:-2], "\r\n"
    if s.endswith("\n"):
        return s[:-1], "\n"
    return s, ""


def transform_line(line: str) -> tuple[str, bool]:
    """
    Remove **...** inside header lines. Returns (new_line, changed?),
    preserving the original line ending (\n or \r\n).
    """
    body, eol = _split_eol(line)
    m = PATTERN.match(body)
    if not m:
        return line, False
    prefix, bold_text, suffix = m.groups()
    return f"{prefix}{bold_text}{suffix}{eol}", True


def iter_files(
    paths: list[Path], recursive: bool, ext: tuple[str, ...]
) -> Iterable[Path]:
    """Yield Markdown files from provided paths."""
    if not paths:
        paths = [Path(".")]
    for p in paths:
        if p.is_file():
            if p.suffix.lower() in ext:
                yield p
        elif p.is_dir():
            if recursive:
                yield from (
                    f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in ext
                )
            else:
                yield from (
                    f for f in p.glob("*") if f.is_file() and f.suffix.lower() in ext
                )


def process_file(
    path: Path,
    allowed_levels: Set[int] | None,
    dry_run: bool = False,
    backup: bool = False,
    encoding: str = "utf-8",
) -> tuple[int, bool]:
    """Process a single file. Returns (num_changes, written?)."""
    try:
        original = path.read_text(encoding=encoding)
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}", file=sys.stderr)
        return 0, False

    changes = 0
    out_lines: list[str] = []
    for line in original.splitlines(keepends=True):
        if levels_filter(line, allowed_levels):
            new_line, changed = transform_line(line)
            if changed:
                changes += 1
                out_lines.append(new_line)
                continue
        out_lines.append(line)

    if changes == 0:
        return 0, False

    if dry_run:
        return changes, False

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        try:
            bak.write_text(original, encoding=encoding)
        except Exception as e:
            print(f"[ERROR] Backup failed {bak}: {e}", file=sys.stderr)
            return 0, False

    new_content = "".join(out_lines)
    try:
        path.write_text(new_content, encoding=encoding)
    except Exception as e:
        print(f"[ERROR] Write failed {path}: {e}", file=sys.stderr)
        return 0, False

    return changes, True


def parse_levels(s: str | None) -> Set[int] | None:
    """Parse comma-separated header levels (e.g., '2,3,4')."""
    if not s:
        return None
    levels = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            n = int(part)
            if 1 <= n <= 6:
                levels.add(n)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid level: {part}")
    return levels or None


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Remove **...** markers that appear directly inside Markdown headers (# ...)."
    )
    ap.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or folders. Default: current directory.",
    )
    ap.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively scan directories."
    )
    ap.add_argument(
        "-e",
        "--ext",
        default=".md,.markdown",
        help="Comma-separated file extensions (default: .md,.markdown).",
    )
    ap.add_argument(
        "-L",
        "--levels",
        default=None,
        help="Allowed header levels (e.g. '3' or '2,3,4'). Default: all (1–6).",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing files."
    )
    ap.add_argument(
        "--no-backup", action="store_true", help="Do not create .bak backups."
    )
    ap.add_argument(
        "--encoding", default="utf-8", help="File encoding (default: utf-8)."
    )

    args = ap.parse_args()
    allowed_levels = parse_levels(args.levels)
    # normalize and validate extensions
    raw_parts = [p.strip().lower() for p in args.ext.split(",") if p.strip()]
    exts: tuple[str, ...] = tuple(
        p if p.startswith(".") else f".{p}" for p in raw_parts
    )

    total_files = 0
    total_changes = 0
    written_files = 0

    for file in iter_files(args.paths, args.recursive, exts):
        total_files += 1
        changes, wrote = process_file(
            file,
            allowed_levels=allowed_levels,
            dry_run=args.dry_run,
            backup=not args.no_backup,
            encoding=args.encoding,
        )
        if changes:
            print(
                f"[OK] {file}: {changes} change(s){' (dry-run)' if args.dry_run else ''}"
            )
            total_changes += changes
        if wrote:
            written_files += 1

    if total_files == 0:
        print("[INFO] No matching files found.", file=sys.stderr)

    print(
        f"\nSummary: scanned={total_files}, changes={total_changes}, written={written_files}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
