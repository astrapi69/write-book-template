#!/usr/bin/env python3
"""
convert_to_absolute.py

Convert relative Markdown image paths to absolute filesystem paths.

Features
- Matches standard Markdown image syntax: ![alt](path "optional title")
- Handles angle-bracketed targets: ![alt](<assets/a(b).png>)
- Skips already-absolute paths
- Only rewrites if the resolved path exists on disk
- Avoids changing image syntax inside fenced code blocks (```...```)
  and inline code (`...`)
- Writes files only if content changed
- Testable: core functions exposed and no cwd side effects at import time
"""

from __future__ import annotations
from pathlib import Path
import argparse
import os
import re
from typing import Iterable, Tuple, Dict

# Fenced + inline code protection (so we don't modify examples in code)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")

# Markdown image: alt, target, optional "title"
# Prefer angle-bracketed target if present to support parentheses inside URLs
# --- replace the MD_IMG_RE with this (adds single-quoted titles) ---
MD_IMG_RE = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\('
    r'(?P<target><.*?>|[^)"]*?)'
    r'(?P<title>\s+(?:"[^"]*"|\'[^\']*\'))?'
    r'\)',
    flags=re.IGNORECASE,
)

# --- add this helper near other utils ---
URLISH_RE = re.compile(r'^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)')

def _is_url_like(target: str) -> bool:
    """Return True if target looks like a URL (http:, https:, data:, mailto:, //cdn, etc.)."""
    return bool(URLISH_RE.match(target))


# Default directories (kept compatible with your original script)
DEFAULT_DIRECTORIES = [
    Path("manuscript") / "chapters",
    Path("manuscript") / "front-matter",
    Path("manuscript") / "back-matter",
]


def _protect_segments(text: str) -> Tuple[str, Dict[str, str]]:
    """Replace fenced and inline code blocks with tokens to avoid touching them."""
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


def _strip_angle_brackets(s: str) -> str:
    return s[1:-1] if s.startswith("<") and s.endswith(">") else s


def _convert_images_in_text(md_text: str, md_file: Path) -> Tuple[str, int]:
    """
    Convert relative image targets inside a single Markdown text to absolute paths.
    Only convert when the resolved absolute path exists.
    Returns (new_text, num_converted).
    """
    protected, mapping = _protect_segments(md_text)
    converted = 0

    def repl(m: re.Match) -> str:
        nonlocal converted
        alt = m.group("alt")
        target_raw = m.group("target")
        title = m.group("title") or ""

        target = _strip_angle_brackets(target_raw).strip()

        # If already absolute filesystem path or URL-like, keep as-is
        if os.path.isabs(target) or _is_url_like(target):
            return m.group(0)

        # Resolve relative to the markdown file directory
        abs_candidate = (md_file.parent / target).resolve()
        if abs_candidate.exists():
            converted += 1
            # Normalize rebuild; keep title and alt as captured
            return f'![{alt}]({abs_candidate}{title})' if title else f'![{alt}]({abs_candidate})'
        else:
            # Leave untouched if it doesn't exist (avoid breaking broken refs differently)
            return m.group(0)

    out = MD_IMG_RE.sub(repl, protected)
    out = _restore_segments(out, mapping)
    return out, converted


def convert_file_to_absolute(md_file: Path) -> Tuple[bool, int]:
    """
    Convert a single .md file. Returns (changed, num_converted).
    Only writes if content changed.
    """
    original = md_file.read_text(encoding="utf-8")
    updated, count = _convert_images_in_text(original, md_file)
    if updated != original:
        md_file.write_text(updated, encoding="utf-8")
        return True, count
    return False, 0


def convert_to_absolute(directories: Iterable[Path]) -> Tuple[int, int]:
    """
    Convert relative image paths to absolute across multiple directories.

    Args:
        directories: Iterable of directories to scan (relative to cwd or absolute)

    Returns:
        (files_changed, images_converted)
    """
    files_changed = 0
    images_converted = 0

    for md_dir in directories:
        md_dir = Path(md_dir).resolve()
        if not md_dir.exists():
            print(f"⚠️ Skipping non-existent directory: {md_dir}")
            continue

        for md_file in md_dir.rglob("*.md"):
            changed, count = convert_file_to_absolute(md_file)
            if changed:
                files_changed += 1
                images_converted += count

    if files_changed:
        print(f"✅ Updated {files_changed} file(s), converted {images_converted} image path(s) to absolute.")
    else:
        print("ℹ️ No changes made (no convertible relative image paths found).")

    return files_changed, images_converted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert relative image paths in Markdown files to absolute paths."
    )
    parser.add_argument(
        "directories",
        nargs="*",
        default=[str(d) for d in DEFAULT_DIRECTORIES],
        help="Directories to scan (default: manuscript/chapters, front-matter, back-matter)",
    )
    args = parser.parse_args()

    dirs = [Path(d) for d in args.directories]
    convert_to_absolute(dirs)


if __name__ == "__main__":
    main()
