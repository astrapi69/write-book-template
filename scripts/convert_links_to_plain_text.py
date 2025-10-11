#!/usr/bin/env python3
# scripts/convert_links_to_plain_text.py
"""
convert_links_to_plain_text.py

Convert Markdown inline links [Label](URL) to print-friendly "Label: URL" text.

- Skips images (![...])
- Skips links in code blocks and inline code
- Drops optional link titles
- Keeps FILE_PATHS list so you can change which files to process easily
"""

from __future__ import annotations
from pathlib import Path
import re
from typing import Tuple, Dict, Iterable

# Target file paths for print conversion (configurable)
FILE_PATHS = [
    Path("./manuscript/back-matter/about-the-author.md"),
]

# Regex patterns
# Prefer an angle-bracketed target <...> if present; otherwise match up to the closing ')'
MD_LINK_RE = re.compile(r"(?<!\!)\[(?P<label>.*?)\]\((?P<target><.*?>|[^)]*?)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _protect_segments(text: str) -> Tuple[str, Dict[str, str]]:
    """Replace code segments with tokens to skip conversion."""
    mapping: Dict[str, str] = {}
    idx = 0

    def protect(pattern: re.Pattern, prefix: str, s: str) -> str:
        nonlocal idx

        def repl(m: re.Match) -> str:
            nonlocal idx
            token = f"{{{{{prefix}_{idx}}}}}"
            mapping[token] = m.group(0)
            idx += 1
            return token

        return pattern.sub(repl, s)

    tmp = protect(FENCE_RE, "FENCE", text)
    tmp = protect(INLINE_CODE_RE, "INLINE", tmp)
    return tmp, mapping


def _restore_segments(text: str, mapping: Dict[str, str]) -> str:
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


def _clean_target(target: str) -> str:
    t = target.strip()
    if " " in t and not (t.startswith("<") and t.endswith(">")):
        t = t.split(" ", 1)[0]
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1]
    return t


def convert_links_in_text(text: str) -> Tuple[str, int]:
    """Convert all Markdown links to print-friendly form in a text string."""
    protected, mapping = _protect_segments(text)
    converted = 0

    def repl(m: re.Match) -> str:
        nonlocal converted
        label = m.group("label")
        target = _clean_target(m.group("target"))
        if not target or target.startswith("#"):
            return m.group(0)
        converted += 1
        return f"{label}: {target}"

    result = MD_LINK_RE.sub(repl, protected)
    return _restore_segments(result, mapping), converted


def convert_file(filepath: Path) -> Tuple[bool, int]:
    """Convert links in a single file. Returns (changed, num_converted)."""
    original = filepath.read_text(encoding="utf-8")
    updated, count = convert_links_in_text(original)
    if updated != original:
        filepath.write_text(updated, encoding="utf-8")
        print(f"✓ Converted links to print-safe format in: {filepath}")
        return True, count
    return False, 0


def convert_many(filepaths: Iterable[Path]) -> Tuple[int, int]:
    """Convert links in multiple files. Returns (files_changed, total_converted)."""
    files_changed = 0
    total_converted = 0
    for fp in filepaths:
        if fp.exists():
            changed, count = convert_file(fp)
            if changed:
                files_changed += 1
                total_converted += count
        else:
            print(f"❌ File not found: {fp}")
    return files_changed, total_converted


if __name__ == "__main__":
    changed, total = convert_many(FILE_PATHS)
    print(f"✅ Converted {total} link(s) across {changed} file(s).")
