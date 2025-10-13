#!/usr/bin/env python3
# scripts/bulk_change_extension.py
"""
Bulk-change file extensions (e.g., .png -> .jpg) without touching file content.

Features
- Generic: any source -> destination extension
- Optional recursion into subfolders
- Case-insensitive matching by default
- Dry-run mode (no changes)
- Safe conflict handling (skip or overwrite)
- Deterministic processing order for predictable results
"""

from __future__ import annotations
import argparse
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass
class RenameResult:
    processed: int = 0
    renamed: int = 0
    skipped_conflict: int = 0
    skipped_nonmatch: int = 0
    errors: int = 0
    planned: int = 0  # for dry-run reporting
    changed_paths: List[Tuple[Path, Path]] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        # Convert Paths to strings for easy JSON/printing
        d["changed_paths"] = [(str(a), str(b)) for a, b in (self.changed_paths or [])]
        return d


def _norm_ext(ext: str) -> str:
    """
    Normalize an extension string to include a leading dot and no trailing whitespace.
    Does not lowercase; caller controls case-insensitive behavior.
    """
    ext = ext.strip()
    if not ext.startswith("."):
        ext = "." + ext
    return ext


def iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    return sorted(root.rglob("*") if recursive else root.glob("*"))


def change_extension(
    target_dir: Path,
    source_ext: str,
    dest_ext: str,
    *,
    recursive: bool = False,
    case_insensitive: bool = True,
    dry_run: bool = False,
    overwrite: bool = False,
) -> RenameResult:
    """
    Rename files ending with `source_ext` to `dest_ext` inside `target_dir`.

    Only the filename suffix is changed. File content is untouched.

    Parameters
    ----------
    target_dir : Path
        Directory to scan.
    source_ext : str
        Source extension, with or without leading dot (e.g., ".png" or "png").
    dest_ext : str
        Destination extension, with or without leading dot (e.g., ".jpg" or "jpg").
    recursive : bool
        If True, process subdirectories.
    case_insensitive : bool
        If True (default), match the source extension case-insensitively.
    dry_run : bool
        If True, do not modify the filesystem; only report what would change.
    overwrite : bool
        If True, overwrite/replace existing destination files. If False, skip conflicts.

    Returns
    -------
    RenameResult
        Summary of actions taken (or planned if dry_run=True).
    """
    result = RenameResult(changed_paths=[])
    if not target_dir.exists():
        print(f"❌ Directory does not exist: {target_dir}", file=sys.stderr)
        result.errors += 1
        return result
    if not target_dir.is_dir():
        print(f"❌ Not a directory: {target_dir}", file=sys.stderr)
        result.errors += 1
        return result

    src_ext = _norm_ext(source_ext)
    dst_ext = _norm_ext(dest_ext)

    files = iter_files(target_dir, recursive)
    for p in files:
        if not p.is_file():
            continue
        result.processed += 1

        suffix = p.suffix
        match = (
            suffix.lower() == src_ext.lower() if case_insensitive else suffix == src_ext
        )
        if not match:
            result.skipped_nonmatch += 1
            continue

        new_path = p.with_suffix(dst_ext)

        if new_path.exists():
            if not overwrite:
                # Skip conflict
                result.skipped_conflict += 1
                print(f"⏭️  Skip (exists): {p.name} → {new_path.name}")
                continue
            # Overwrite: remove the existing target file
            if not dry_run:
                try:
                    new_path.unlink()
                except Exception as e:
                    print(
                        f"❌ Failed to remove existing target '{new_path}': {e}",
                        file=sys.stderr,
                    )
                    result.errors += 1
                    continue

        # Plan or perform rename
        result.planned += 1
        result.changed_paths.append((p, new_path))
        if dry_run:
            print(
                f"🔎 (dry-run) {p.relative_to(target_dir)} → {new_path.relative_to(target_dir)}"
            )
        else:
            try:
                p.rename(new_path)
                print(
                    f"🔄 {p.relative_to(target_dir)} → {new_path.relative_to(target_dir)}"
                )
                result.renamed += 1
            except Exception as e:
                print(f"❌ Failed to rename '{p}' → '{new_path}': {e}", file=sys.stderr)
                result.errors += 1

    if dry_run:
        print(f"✅ Dry-run complete: {result.planned} file(s) would be changed.")
    else:
        print(
            f"✅ Rename complete: {result.renamed} file(s) changed. "
            f"{result.skipped_conflict} conflict(s) skipped. {result.errors} error(s)."
        )

    return result


def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Bulk-change file extensions without modifying content."
    )
    ap.add_argument("directory", help="Target directory to process.")
    ap.add_argument(
        "--from", dest="src", required=True, help="Source extension (e.g., .png)"
    )
    ap.add_argument(
        "--to", dest="dst", required=True, help="Destination extension (e.g., .jpg)"
    )
    ap.add_argument(
        "-r", "--recursive", action="store_true", help="Recurse into subdirectories"
    )
    ap.add_argument(
        "--case-sensitive",
        dest="case_sensitive",
        action="store_true",
        help="Match source extension case-sensitively (default: case-insensitive)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed, but do nothing",
    )
    ap.add_argument(
        "--overwrite", action="store_true", help="Overwrite if destination exists"
    )
    return ap.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])
    result = change_extension(
        Path(ns.directory),
        ns.src,
        ns.dst,
        recursive=ns.recursive,
        case_insensitive=not ns.case_sensitive,
        dry_run=ns.dry_run,
        overwrite=ns.overwrite,
    )
    # Exit non-zero if any error occurred
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
