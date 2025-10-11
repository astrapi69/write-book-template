#!/usr/bin/env python3
# scripts/convert_img_tags.py
"""
convert_img_tags.py

Convert <img> src paths in Markdown files between relative and absolute.

- Scans manuscript/* subfolders (chapters, front-matter, back-matter) by default.
- Preserves other <img> attributes.
- Supports single or double quotes around attribute values.
- Writes files only when content actually changes.
- Testable: core functions accept base_dir and directories explicitly.

CLI:
  python3 scripts/convert_img_tags.py --to-absolute
  python3 scripts/convert_img_tags.py --to-relative
"""

from __future__ import annotations
from pathlib import Path
import argparse
import os
import re
from typing import Iterable, Tuple

# Generic <img> matcher; we’ll parse attributes separately
IMG_TAG_RE = re.compile(r"<img\b([^>]*)>", flags=re.IGNORECASE)

# Attribute parser: key="value" or key='value' with optional whitespace
# Old: ATTR_RE = re.compile(r'(\w+)\s*=\s*("([^"]*)"|\'([^\']*)\')')
ATTR_RE = re.compile(r'([A-Za-z_:][A-Za-z0-9:._-]*)\s*=\s*("([^"]*)"|\'([^\']*)\')')


def parse_img_attributes(attr_text: str) -> dict[str, str]:
    """
    Parse attributes inside an <img ...> tag into a dict.
    Last occurrence of a duplicate key wins (HTML behavior is undefined; we choose last).
    """
    attrs: dict[str, str] = {}
    for m in ATTR_RE.finditer(attr_text):
        key = m.group(1).lower()
        value = (
            m.group(3) if m.group(3) is not None else m.group(4)
        )  # prefer group3 (") else group4 (')
        attrs[key] = value
    return attrs


def build_img_tag(attrs: dict[str, str]) -> str:
    """
    Rebuild a normalized <img ...> tag from attributes.
    We keep src first, alt second, then the rest in alpha order for stability.
    Always ensure a single space after <img> when attributes exist.
    """
    ordered = []
    if "src" in attrs:
        ordered.append(("src", attrs["src"]))
    if "alt" in attrs:
        ordered.append(("alt", attrs["alt"]))
    for k in sorted(k for k in attrs.keys() if k not in {"src", "alt"}):
        ordered.append((k, attrs[k]))

    inside = " ".join(f'{k}="{v}"' for k, v in ordered)
    # If there are attributes, ensure exactly one space after <img>
    return f"<img{' ' if inside else ''}{inside}>"


def _convert_src_for_file(
    md_file: Path, to_absolute: bool, assets_dir: Path
) -> tuple[str, int]:
    original = md_file.read_text(encoding="utf-8")
    converted = 0

    def repl(match: re.Match) -> str:
        nonlocal converted
        raw_attrs = match.group(1) or ""
        attrs = parse_img_attributes(raw_attrs)

        if "src" not in attrs:
            return match.group(0)

        src = attrs["src"]
        if to_absolute:
            if not os.path.isabs(src):
                candidate = (md_file.parent / src).resolve()
                if candidate.exists():
                    attrs["src"] = str(candidate)
                    converted += 1
        else:
            p = Path(src)
            # Support both 3.10+ and fallback
            try:
                if p.is_absolute() and p.resolve().is_relative_to(assets_dir.resolve()):
                    rel = os.path.relpath(str(p), start=str(md_file.parent))
                    attrs["src"] = rel
                    converted += 1
            except AttributeError:
                p_res = p.resolve()
                a_res = assets_dir.resolve()
                try:
                    p_res.relative_to(a_res)
                    rel = os.path.relpath(str(p_res), start=str(md_file.parent))
                    attrs["src"] = rel
                    converted += 1
                except ValueError:
                    pass

        return build_img_tag(attrs)

    new_content = IMG_TAG_RE.sub(repl, original)
    return new_content, converted


def convert_markdown_tree(
    base_dir: Path,
    md_directories: Iterable[Path] | None = None,
    to_absolute: bool = True,
    assets_dir: Path | None = None,
) -> Tuple[int, int]:
    """
    Convert <img> src across a set of markdown directories.

    Args:
        base_dir: Project root.
        md_directories: Iterable of directories to scan (relative or absolute).
        to_absolute: True to convert relative->absolute, False to convert absolute->relative.
        assets_dir: Base assets directory (required for to_relative).

    Returns:
        (files_changed, tags_converted)
    """
    base_dir = base_dir.resolve()
    if md_directories is None:
        md_directories = [
            base_dir / "manuscript" / "chapters",
            base_dir / "manuscript" / "front-matter",
            base_dir / "manuscript" / "back-matter",
        ]
    if assets_dir is None:
        assets_dir = base_dir / "assets"

    files_changed = 0
    tags_converted = 0

    for md_dir in md_directories:
        md_dir = (base_dir / md_dir) if not Path(md_dir).is_absolute() else Path(md_dir)
        if not md_dir.exists():
            continue
        for md_file in md_dir.rglob("*.md"):
            new_content, converted = _convert_src_for_file(
                md_file, to_absolute=to_absolute, assets_dir=assets_dir
            )
            if converted > 0:
                md_file.write_text(new_content, encoding="utf-8")
                files_changed += 1
                tags_converted += converted

    return files_changed, tags_converted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert <img> src paths between relative and absolute."
    )
    parser.add_argument(
        "--to-absolute",
        action="store_true",
        help="Convert relative paths to absolute paths.",
    )
    parser.add_argument(
        "--to-relative",
        action="store_true",
        help="Convert absolute paths (under assets/) to relative paths.",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=str(Path(__file__).resolve().parent.parent),
        help="Project root (defaults to repository root).",
    )
    args = parser.parse_args()

    base = Path(args.base_dir).resolve()
    assets = base / "assets"

    if args.to_absolute == args.to_relative:
        print("❌ Please specify exactly one of --to-absolute or --to-relative.")
        raise SystemExit(2)

    to_abs = bool(args.to_absolute)
    changed, converted = convert_markdown_tree(
        base, to_absolute=to_abs, assets_dir=assets
    )
    if to_abs:
        print(
            f"✅ Converted {converted} <img> tag(s) to absolute across {changed} file(s)."
        )
    else:
        print(
            f"🔄 Reverted {converted} <img> tag(s) to relative across {changed} file(s)."
        )


if __name__ == "__main__":
    main()
