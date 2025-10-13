# scripts/sanitize.py
from __future__ import annotations
import argparse
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from typing import Set
from pathlib import Path

import ftfy

CONTROL_CHARS_RE = re.compile(
    r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]"
)  # keep \t(0009) and \n(000A) and \r(000D) out; we'll normalize \r\n separately

# “Format” controls except keep ZWJ/ZWNJ if you rely on them; default: remove
FORMAT_CHARS = {
    "\u200b",  # ZWSP
    "\u200c",  # ZWNJ
    "\u200d",  # ZWJ
    "\u200e",  # LRM
    "\u200f",  # RLM
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",  # embedding/override
    "\ufeff",  # BOM
}

DANGEROUS_MAP = {
    "\u00ad": "",  # soft hyphen
    "\u2028": "\n",  # line separator → newline
    "\u2029": "\n",  # paragraph separator → newline
    "\u202f": " ",  # narrow no‑break space
    "\u00a0": " ",  # no‑break space
}


@dataclass
class Stats:
    files_seen: int = 0
    files_changed: int = 0
    errors: int = 0


def sanitize_markdown(text: str) -> str:
    # 1) Fix mojibake etc.
    text = ftfy.fix_text(text)

    # 2) Unicode normalization (NFKC tends to be best for plain text)
    text = unicodedata.normalize("NFKC", text)

    # 3) Replace “dangerous” chars
    for ch, repl in DANGEROUS_MAP.items():
        text = text.replace(ch, repl)

    # 4) Remove format controls
    for ch in FORMAT_CHARS:
        text = text.replace(ch, "")

    # 5) Strip other control chars (but keep \n and \t)
    text = CONTROL_CHARS_RE.sub("", text)

    # 6) Normalize newlines → \n and ensure single trailing newline
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    return text


def process_file(path: Path, *, dry_run: bool, backup: bool) -> bool:
    original = path.read_text(encoding="utf-8", errors="strict")
    cleaned = sanitize_markdown(original)
    if cleaned != original:
        if backup:
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        if not dry_run:
            path.write_text(cleaned, encoding="utf-8")
        return True
    return False


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Sanitize Markdown in a directory.")
    p.add_argument("--root", default="manuscript", help="Root directory to scan")
    p.add_argument("--include", default="**/*.md", help="Glob to include")
    p.add_argument(
        "--exclude", action="append", default=[], help="Glob(s) to exclude (repeatable)"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Show changes but do not write files"
    )
    p.add_argument(
        "--backup", action="store_true", help="Create .bak alongside modified files"
    )
    args = p.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"❌ Error: Directory '{root}' not found.")
        sys.exit(1)

    stats = Stats()
    files = sorted(root.glob(args.include))
    # apply excludes
    excluded: Set[Path] = set()
    for pattern in args.exclude:
        excluded.update(root.glob(pattern))
    files = [f for f in files if f.is_file() and f not in excluded]

    if not files:
        print(f"⚠️  No Markdown files for pattern {args.include} in {root}")
        return

    for md in files:
        stats.files_seen += 1
        try:
            changed = process_file(md, dry_run=args.dry_run, backup=args.backup)
            if changed:
                verb = "WOULD clean" if args.dry_run else "Cleaned"
                print(f"✅ {verb}: {md}")
                stats.files_changed += 1
            else:
                print(f"🟢 No changes: {md}")
        except Exception as e:
            print(f"❌ Failed to process {md}: {e}")
            stats.errors += 1

    print(
        f"\n✨ Done! Seen: {stats.files_seen} • "
        f"Changed: {stats.files_changed} • Errors: {stats.errors} "
        f"{'(dry-run)' if args.dry_run else ''}"
    )


if __name__ == "__main__":
    main()
