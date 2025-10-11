#!/usr/bin/env python3
# scripts/convert_to_absolute.py
"""
convert_to_absolute.py

Convert relative Markdown image paths to absolute filesystem paths.

Features
- Matches standard Markdown image syntax: ![alt](path ["optional title"] or ['optional title'])
- Handles angle-bracketed targets: ![alt](<assets/a(b).png> "Cover")
- Balances parentheses in bare URLs (e.g. /a(b)/c.png) via a tiny scanner (no regex guesswork)
- Skips already-absolute paths and URL-like targets (http:, https:, mailto:, data:, //cdn, etc.)
- Avoids changing image syntax inside fenced code blocks (```...```) and inline code (`...`)
- Writes files only if content changed
- Testable: no cwd side effects at import time, clean API
"""

from __future__ import annotations
from pathlib import Path
import argparse
import os
import re
from typing import Iterable, Tuple, Dict, Optional, List

# -----------------------
# Code / inline protection
# -----------------------

FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


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


# -----------------------
# URL-like detection
# -----------------------

URLISH_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)")


def _is_url_like(target: str) -> bool:
    """Return True if target looks like a URL (http:, https:, data:, mailto:, //cdn, etc.)."""
    return bool(URLISH_RE.match(target))


# -----------------------
# Image tag scanner
# -----------------------


def _find_image_tag(text: str, start: int) -> Optional[Tuple[int, int, str, str]]:
    """
    Find the next well-formed Markdown image starting at or after `start`.

    Returns:
        (tag_start, tag_end_exclusive, alt_text, inside_parens)
    or None if not found.
    """
    pos = start
    n = len(text)
    while True:
        i = text.find("![", pos)
        if i == -1:
            return None

        # parse alt text
        j = text.find("]", i + 2)
        if j == -1:
            # malformed; skip past this '![', keep searching
            pos = i + 2
            continue
        if j + 1 >= n or text[j + 1] != "(":
            # not an image tag; skip past this '![', keep searching
            pos = i + 2
            continue

        # scan inside (...) with simple balance + angle-bracket awareness
        k = j + 2  # position after '('
        depth = 0
        in_angle = False
        while k < n:
            ch = text[k]

            # Enter <...> only at top-level (not inside nested ())
            if not in_angle and depth == 0 and ch == "<":
                in_angle = True
                k += 1
                continue

            # While inside <...>, ignore all chars except closing '>'
            if in_angle:
                if ch == ">":
                    in_angle = False
                k += 1
                continue

            if ch == "(":
                depth += 1
                k += 1
                continue

            if ch == ")":
                if depth == 0:
                    # closing of the image tag
                    alt = text[i + 2 : j]
                    inside = text[j + 2 : k]
                    return (i, k + 1, alt, inside)
                depth -= 1
                k += 1
                continue

            k += 1

        # Reaching here means we never found the closing ')' for this candidate -> malformed.
        # Skip past this '![', keep searching for the next image.
        pos = i + 2


def _split_inside_parens(inside: str) -> Tuple[str, str]:
    """
    Split 'inside' (everything between '(' and ')') into (target, title_part).

    Supports:
    - <angle-bracketed> target + optional quoted title
    - bare targets with balanced parentheses, then optional quoted title ("..." or '...')
    - allows spaces in the target (we only stop when we see a quoted title at top-level)
    """
    s = inside.strip()
    if not s:
        return "", ""

    # <angle-bracketed> target first (optionally followed by quoted title)
    m = re.match(r'^(<[^>]+>)(?P<rest>\s+(?:"[^"]*"|\'[^\']*\'))?\s*$', s)
    if m:
        return m.group(1), (m.group("rest") or "")

    # bare target with optional title:
    target_chars: List[str] = []
    depth = 0
    i = 0
    n = len(s)
    title_part = ""
    while i < n:
        ch = s[i]
        if ch == "(":
            depth += 1
            target_chars.append(ch)
            i += 1
            continue
        if ch == ")":
            # allow unmatched ')' as a URL char (Markdown usually requires <...> in this case,
            # but we keep it permissive to handle real-world docs)
            if depth == 0:
                target_chars.append(ch)
                i += 1
                continue
            depth -= 1
            target_chars.append(ch)
            i += 1
            continue
        if depth == 0 and ch.isspace():
            # lookahead: quoted title?
            j = i
            while j < n and s[j].isspace():
                j += 1
            if j < n and s[j] in ('"', "'"):
                title_part = " " + s[j:]
                break
            # otherwise include whitespace in URL
            target_chars.append(ch)
            i += 1
            continue
        target_chars.append(ch)
        i += 1

    return "".join(target_chars).rstrip(), title_part


def _strip_angle_brackets(s: str) -> str:
    return s[1:-1] if s.startswith("<") and s.endswith(">") else s


# -----------------------
# Conversion core
# -----------------------


def _convert_images_in_text(md_text: str, md_file: Path) -> Tuple[str, int]:
    """
    Convert relative image targets inside a single Markdown text to absolute paths.
    Only convert when the resolved absolute path exists.
    Returns (new_text, num_converted).
    """
    protected, mapping = _protect_segments(md_text)
    out_parts: List[str] = []
    idx = 0
    converted = 0

    while True:
        found = _find_image_tag(protected, idx)
        if not found:
            out_parts.append(protected[idx:])  # rest
            break

        tag_start, tag_end, alt, inside = found
        # append text before tag
        out_parts.append(protected[idx:tag_start])

        raw_target, title_part = _split_inside_parens(inside)
        if not raw_target:
            # write back original slice if we couldn't parse
            out_parts.append(protected[tag_start:tag_end])
            idx = tag_end
            continue

        target = _strip_angle_brackets(raw_target).strip()

        # Skip if URL-like (http:, data:, //cdn, mailto:, etc.) or already absolute fs path
        if _is_url_like(target) or os.path.isabs(target):
            out_parts.append(protected[tag_start:tag_end])
            idx = tag_end
            continue

        abs_candidate = (md_file.parent / target).resolve()
        if abs_candidate.exists():
            converted += 1
            # title_part already includes leading space if present
            out_parts.append(f"![{alt}]({abs_candidate}{title_part})")
        else:
            # leave untouched
            out_parts.append(protected[tag_start:tag_end])

        idx = tag_end

    result = "".join(out_parts)
    result = _restore_segments(result, mapping)
    return result, converted


# -----------------------
# Public API
# -----------------------


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


DEFAULT_DIRECTORIES = [
    Path("manuscript") / "chapters",
    Path("manuscript") / "front-matter",
    Path("manuscript") / "back-matter",
]


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
        print(
            f"✅ Updated {files_changed} file(s), converted {images_converted} image path(s) to absolute."
        )
    else:
        print("ℹ️ No changes made (no convertible relative image paths found).")

    return files_changed, images_converted


# -----------------------
# CLI
# -----------------------


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
