#!/usr/bin/env python3
# scripts/convert_images.py
"""
convert_images.py
-----------------
Convert Markdown image syntax into HTML <figure> blocks.

- Works recursively on directories (e.g. manuscript/).
- Skips fenced code blocks (``` or ~~~) and inline code (`...`).
- Supports inline and reference-style images.
- Uses image title as caption if present, otherwise alt text.
"""

from __future__ import annotations
import argparse
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Sequence

FIGURE_TEMPLATE = """<figure{klass}>
  <img src="{src}" alt="{alt}" />
  <figcaption>
    <em>{caption}</em>
  </figcaption>
</figure>"""

# --- Regexes ---
IMG_INLINE_RE = re.compile(
    r"""
    !\[(?P<alt>[^\]]*)\]
    \(
        \s*
        (?P<rawsrc>\<[^>]*\>|[^)\s]+)
        (?:
            \s+
            (?:
                "(?P<title_dq>[^"]*)"
                | '(?P<title_sq>[^']*)'
                | \((?P<title_par>[^)]*)\)
            )
        )?
        \s*
    \)
    """,
    re.VERBOSE,
)
IMG_REF_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\[(?P<id>[^\]]*)\]", re.VERBOSE)
REF_DEF_RE = re.compile(
    r"""
    ^\[(?P<id>[^\]]+)\]:
        \s*(?P<rawsrc>\<[^>]*\>|[^ \t]+)
        (?:
            \s+
            (?:
                "(?P<title_dq>[^"]*)"
                | '(?P<title_sq>[^']*)'
                | \((?P<title_par>[^)]*)\)
            )
        )?
        \s*$
    """,
    re.VERBOSE | re.MULTILINE,
)
CODE_FENCE_RE = re.compile(r"(^|\n)(`{3,}|~{3,}).*?\n\2[^\S\r\n]*?(?=\n|$)", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _unangle(url: str) -> str:
    url = url.strip()
    return url[1:-1].strip() if url.startswith("<") and url.endswith(">") else url


def _caption(alt: str, title: str | None) -> str:
    return title.strip() if title and title.strip() else alt


def _parse_ref_defs(text: str) -> Dict[str, dict]:
    refs = {}
    for m in REF_DEF_RE.finditer(text):
        rid = m.group("id").strip().lower()
        rawsrc = m.group("rawsrc")
        title = m.group("title_dq") or m.group("title_sq") or m.group("title_par")
        refs[rid] = {"src": _unangle(rawsrc), "title": title}
    return refs


def _split_outside_code(text: str) -> List[Tuple[bool, str]]:
    """Return list of (is_code, segment)."""
    segments: List[Tuple[bool, str]] = []
    last = 0
    for m in CODE_FENCE_RE.finditer(text):
        if m.start() > last:
            segments.append((False, text[last : m.start()]))
        segments.append((True, m.group(0)))
        last = m.end()
    if last < len(text):
        segments.append((False, text[last:]))

    # also split inline code
    refined: List[Tuple[bool, str]] = []
    for is_code, seg in segments:
        if is_code:
            refined.append((True, seg))
        else:
            pos = 0
            for im in INLINE_CODE_RE.finditer(seg):
                if im.start() > pos:
                    refined.append((False, seg[pos : im.start()]))
                refined.append((True, im.group(0)))
                pos = im.end()
            if pos < len(seg):
                refined.append((False, seg[pos:]))
    return refined


def _replace_inline(chunk: str, figure_class: str | None) -> Tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        alt = (m.group("alt") or "").strip()
        src = _unangle(m.group("rawsrc"))
        title = m.group("title_dq") or m.group("title_sq") or m.group("title_par")
        caption = _caption(alt, title)
        count += 1
        klass = f' class="{figure_class}"' if figure_class else ""
        return FIGURE_TEMPLATE.format(klass=klass, src=src, alt=alt, caption=caption)

    return IMG_INLINE_RE.sub(repl, chunk), count


def _replace_reference(
    chunk: str, refs: Dict[str, dict], figure_class: str | None
) -> Tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        alt = (m.group("alt") or "").strip()
        rid = (m.group("id") or alt).strip().lower()
        ref = refs.get(rid)
        if not ref:
            return m.group(0)
        src = ref["src"]
        caption = _caption(alt, ref["title"])
        count += 1
        klass = f' class="{figure_class}"' if figure_class else ""
        return FIGURE_TEMPLATE.format(klass=klass, src=src, alt=alt, caption=caption)

    return IMG_REF_RE.sub(repl, chunk), count


def convert_markdown_file(
    file_path: Path,
    *,
    backup: bool = False,
    dry_run: bool = False,
    figure_class: str | None = None,
) -> int:
    """Convert a single Markdown file. Returns number of images converted."""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return 0

    text = file_path.read_text(encoding="utf-8")
    refs = _parse_ref_defs(text)
    segments = _split_outside_code(text)

    converted: List[str] = []
    total = 0
    for is_code, chunk in segments:
        if is_code:
            converted.append(chunk)
            continue
        chunk, c1 = _replace_inline(chunk, figure_class)
        chunk, c2 = _replace_reference(chunk, refs, figure_class)
        total += c1 + c2
        converted.append(chunk)

    if total == 0:
        return 0

    new_text = "".join(converted)

    if dry_run:
        print(f"🧪 Dry-Run: {total} images would be converted: {file_path}")
        return total

    if backup:
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy(file_path, backup_path)

    file_path.write_text(new_text, encoding="utf-8")
    print(f"✅ {total} images converted: {file_path}")
    return total


def convert_markdown_dir(
    root: Path,
    *,
    backup: bool = False,
    dry_run: bool = False,
    figure_class: str | None = None,
) -> int:
    """Recursively process all .md files under root."""
    total = 0
    for file in root.rglob("*.md"):
        total += convert_markdown_file(
            file, backup=backup, dry_run=dry_run, figure_class=figure_class
        )
    return total


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Markdown images to <figure> blocks."
    )
    parser.add_argument("input", help="Markdown file or directory")
    parser.add_argument(
        "--backup", action="store_true", help="Create .bak backups before writing"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only count changes, do not write files"
    )
    parser.add_argument(
        "--figure-class", default=None, help="Optional CSS class for <figure>"
    )

    # Backward-compat: accept --no-backup but ignore (backups are off by default)
    parser.add_argument("--no-backup", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)

    path = Path(args.input)
    opts = dict(
        backup=args.backup, dry_run=args.dry_run, figure_class=args.figure_class
    )

    if path.is_file():
        return convert_markdown_file(path, **opts)
    elif path.is_dir():
        return convert_markdown_dir(path, **opts)
    else:
        print(f"❌ Input path not found: {path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
