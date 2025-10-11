#!/usr/bin/env python3
# scripts/strip_links.py
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, Tuple, List, Optional

# Default TOC path to match prior behavior
DEFAULT_TOC = Path("manuscript/front-matter/toc.md")

# Regexes
# Fenced code blocks (```...``` or ~~~...~~~), multiline
FENCED_RX = re.compile(r"(?ms)^(```.*?\n.*?^```|~~~.*?\n.*?^~~~)\s*")
# Inline code spans `...` (no nested backticks)
INLINE_CODE_RX = re.compile(r"`[^`\n]*`")

# Inline Markdown links [text](url) but NOT images ![alt](url)
# Use negative lookbehind to ensure no preceding '!'
LINK_RX = re.compile(r"(?<!\!)\[(?P<text>[^\]]+?)\]\((?P<url>[^)]+?)\)")

# Reference links: [text][id] or [text][]
REF_LINK_RX = re.compile(r"(?<!\!)\[(?P<text>[^\]]+?)\]\[(?P<id>[^\]]*)\]")

# Link definitions (e.g. [id]: https://example.com "Title")
LINK_DEF_RX = re.compile(r"(?m)^\s*\[[^\]]+\]\s*:\s*\S+.*$")


def _strip_links_segment(text: str) -> Tuple[str, int]:
    """Strip [text](url) -> text in a linkable segment (no code present)."""
    count = 0

    def _rep(m: re.Match) -> str:
        nonlocal count
        count += 1
        return m.group("text")

    return LINK_RX.sub(_rep, text), count


def strip_links_in_text(text: str) -> Tuple[str, int]:
    """
    Strip inline links but preserve:
      - images ![alt](url)
      - fenced code blocks (``` / ~~~)
      - inline code spans `...`
    Also removes reference links and link definition lines.
    Returns (new_text, num_links_stripped)
    """
    if not text:
        return text, 0

    # First, locate all fenced blocks and inline code to protect them.
    spans: List[Tuple[int, int]] = []
    for rx in (FENCED_RX, INLINE_CODE_RX):
        for m in rx.finditer(text):
            spans.append((m.start(), m.end()))
    spans.sort()

    # Walk the text, processing only non-protected segments.
    out_parts: List[str] = []
    i = 0
    total = 0
    for s, e in spans:
        if i < s:
            seg, n = strip_links_in_text_no_code(text[i:s])
            out_parts.append(seg)
            total += n
        out_parts.append(text[s:e])  # protected as-is
        i = e
    if i < len(text):
        seg, n = strip_links_in_text_no_code(text[i:])
        out_parts.append(seg)
        total += n

    return "".join(out_parts), total


def strip_links_in_text_no_code(text: str) -> Tuple[str, int]:
    """Helper for non-code segments only: inline + reference links, and remove link definitions."""
    # 1) Inline links [text](url)
    t1, n1 = _strip_links_segment(text)

    # 2) Reference links [text][id] and [text][]
    ref_count = 0

    def _rep_ref(m: re.Match) -> str:
        nonlocal ref_count
        ref_count += 1
        return m.group("text")

    t2 = REF_LINK_RX.sub(_rep_ref, t1)

    # 3) Remove link definition lines (e.g. "[id]: https://...") entirely
    t3, n3 = LINK_DEF_RX.subn("", t2)

    # Normalize excessive blank lines that might result from removing definitions
    t3 = re.sub(r"\n{3,}", "\n\n", t3)

    return t3, n1 + ref_count + n3


def process_file(
    src: Path, overwrite: bool, suffix: str, encoding: str = "utf-8"
) -> Tuple[Path, int, Optional[Path]]:
    """
    Process one file. Returns (src_path, links_stripped, dest_written_or_None).
    - If overwrite=True: writes back to src only if changed.
    - If overwrite=False: writes <stem>{suffix} next to src only if changed.
    """
    original = src.read_text(encoding=encoding)
    replaced, n = strip_links_in_text(original)

    if n == 0:
        return src, 0, None

    if overwrite:
        src.write_text(replaced, encoding=encoding)
        return src, n, src

    dest = src.with_name(src.stem + suffix)
    dest.write_text(replaced, encoding=encoding)
    return src, n, dest


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Strip Markdown links ([text](url), [text][id]) to plain text (skips images and code)."
    )
    ap.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_TOC,
        help="Markdown file to process (default: manuscript/front-matter/toc.md).",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite file in place. Default: write a copy with suffix.",
    )
    ap.add_argument(
        "--suffix",
        default="-nolinks.md",
        help="Suffix for copy mode (default: -nolinks.md).",
    )
    ap.add_argument("--encoding", default="utf-8", help="File encoding.")
    ap.add_argument(
        "--dry-run", action="store_true", help="Print planned changes without writing."
    )
    ap.add_argument(
        "--report", action="store_true", help="Print number of links stripped."
    )
    return ap.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    path = args.file

    if not path.exists():
        print(f"❌ File not found: {path}")
        return 1

    text = path.read_text(encoding=args.encoding)
    new_text, n = strip_links_in_text(text)

    if args.report:
        print(f"[{path}] links_stripped={n}")

    if args.dry_run:
        print("🔎 dry-run: no files written")
        return 0

    if n == 0:
        print(f"✓ No links to strip in: {path.name}")
        return 0

    if args.overwrite:
        path.write_text(new_text, encoding=args.encoding)
        print(f"✓ Stripped links (in place): {path}")
    else:
        dest = path.with_name(path.stem + args.suffix)
        dest.write_text(new_text, encoding=args.encoding)
        print(f"✓ Stripped links: {path.name} → {dest.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
