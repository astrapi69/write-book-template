#!/usr/bin/env python3
# scripts/replace_emojis.py
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Dict, Iterable, Iterator, Tuple

DEFAULT_SECTIONS = ("front-matter", "chapters", "back-matter")
DEFAULT_SUFFIX = "-final.md"
DEFAULT_ENCODING = "utf-8"


# Fallback: local emoji_map.py next to this script (optional)
def _load_default_map() -> Dict[str, str]:
    try:
        from .emoji_map import EMOJI_MAP  # type: ignore

        return dict(EMOJI_MAP)
    except Exception:
        try:
            # If not a package, try sibling import
            from emoji_map import EMOJI_MAP  # type: ignore

            return dict(EMOJI_MAP)
        except Exception:
            return {}


def load_mapping_from_module(module_path: Path | None) -> Dict[str, str]:
    """Load EMOJI_MAP from a python module path, or use default."""
    if module_path is None:
        m = _load_default_map()
        if not m:
            raise RuntimeError(
                "No emoji mapping available. Provide --map or ensure emoji_map.py is importable."
            )
        return m

    spec = importlib.util.spec_from_file_location(
        "emoji_map_external", str(module_path)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import map module from {module_path}")

    assert spec is not None, "ModuleSpec is None"
    assert spec.loader is not None, "ModuleSpec.loader is None"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    try:
        m = getattr(module, "EMOJI_MAP")
    except AttributeError:
        raise RuntimeError(f"{module_path} does not define EMOJI_MAP")
    if not isinstance(m, dict):
        raise RuntimeError("EMOJI_MAP must be a dict[str, str]")
    return dict(m)


def validate_mapping(mapping: Dict[str, str]) -> Tuple[bool, str]:
    """Light sanity check: non-empty keys, no duplicate keys, strings only."""
    if not mapping:
        return False, "Mapping is empty."
    for k, v in mapping.items():
        if not isinstance(k, str) or not isinstance(v, str):
            return False, "All keys/values must be strings."
        if not k:
            return False, "Empty string emoji key detected."
    return True, ""


def replace_emojis_in_text(text: str, mapping: Dict[str, str]) -> Tuple[str, int]:
    """Replace all emojis using a *length-descending* key order to avoid partial overlap."""
    if not text:
        return text, 0
    count = 0
    # Sort by length descending for safety (e.g., multi-codepoint emojis)
    for emoji in sorted(mapping.keys(), key=len, reverse=True):
        repl = mapping[emoji]
        if emoji in text:
            occurrences = text.count(emoji)
            text = text.replace(emoji, repl)
            count += occurrences
    return text, count


def process_file(
    src: Path, overwrite: bool, suffix: str, mapping: Dict[str, str], encoding: str
) -> Tuple[Path, int, Path | None]:
    """Process one file; return (src, num_replacements, dest_if_written_or_None)."""
    original = src.read_text(encoding=encoding)
    replaced, n = replace_emojis_in_text(original, mapping)

    if overwrite:
        if n:
            src.write_text(replaced, encoding=encoding)
        return src, n, src if n else None

    # write side-by-side copy if not overwriting
    dest = src.with_name(src.stem + suffix)
    # Only write the copy if something changed (same behavior as overwrite)
    if n:
        dest.write_text(replaced, encoding=encoding)
        return src, n, dest
    return src, n, None


def iter_md_files(book_dir: Path, sections: Iterable[str]) -> Iterator[Path]:
    for section in sections:
        sp = book_dir / section
        if not sp.exists():
            continue
        yield from (p for p in sp.glob("*.md") if not str(p).endswith(".md.bak"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Replace emojis in Markdown files using a provided mapping."
    )
    ap.add_argument(
        "--book-dir",
        type=Path,
        default=Path("./manuscript"),
        help="Root manuscript directory.",
    )
    ap.add_argument(
        "--sections",
        nargs="*",
        default=list(DEFAULT_SECTIONS),
        help="Sections to scan (folders).",
    )
    ap.add_argument(
        "--suffix",
        default=DEFAULT_SUFFIX,
        help="Suffix for new files when not overwriting.",
    )
    ap.add_argument(
        "--encoding", default=DEFAULT_ENCODING, help="File encoding (default: utf-8)."
    )
    ap.add_argument(
        "--map", type=Path, help="Path to a Python module that defines EMOJI_MAP."
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files in place (default: copy).",
    )
    ap.add_argument("--no-overwrite", dest="overwrite", action="store_false")
    ap.add_argument(
        "--dry-run", action="store_true", help="Print planned changes without writing."
    )
    ap.add_argument(
        "--report", action="store_true", help="Print per-file replacement counts."
    )
    ap.set_defaults(overwrite=False)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mapping = load_mapping_from_module(args.map)
    ok, msg = validate_mapping(mapping)
    if not ok:
        print(f"❌ Invalid mapping: {msg}")
        return 2

    total_files = 0
    total_changes = 0
    wrote = 0

    for md in iter_md_files(args.book_dir, args.sections):
        total_files += 1

        content = md.read_text(encoding=args.encoding)
        new_content, n = replace_emojis_in_text(content, mapping)

        if args.report:
            print(f"[{md.relative_to(args.book_dir)}] replacements={n}")

        if args.dry_run:
            total_changes += n
            continue

        # perform write if needed
        _, n_written, dest = process_file(
            md, args.overwrite, args.suffix, mapping, args.encoding
        )
        total_changes += n_written
        if dest is not None:
            wrote += 1
            print(
                f"✓ {'Overwrote' if args.overwrite else 'Converted'}: {md.name}"
                f"{'' if args.overwrite else f' → {dest.name}'}"
            )

    print(
        f"\nDone. files_scanned={total_files} files_written={wrote} total_replacements={total_changes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
