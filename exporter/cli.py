from __future__ import annotations
from pathlib import Path
import argparse
from .pipeline import build_all, DEFAULT_SECTION_ORDER

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Export book into multiple formats.")
    p.add_argument("--format", type=str, help="Comma-separated formats (pdf,epub,docx,markdown)")
    p.add_argument("--order", type=str, default=",".join(DEFAULT_SECTION_ORDER))
    p.add_argument("--cover", type=str)
    p.add_argument("--epub2", action="store_true")
    p.add_argument("--lang", type=str)
    p.add_argument("--extension", type=str)
    p.add_argument("--book-type", type=str, choices=["ebook","paperback","hardcover"], default="ebook")
    p.add_argument("--output-file", type=str, help="Custom base name (overrides project name)")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--skip-images", action="store_true")
    group.add_argument("--keep-relative-paths", action="store_true")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    formats = args.format.split(",") if args.format else None
    section_order = args.order.split(",")
    build_all(
        root=Path("."),
        formats=formats,
        section_order=section_order,
        book_type=args.book_type,
        output_file_cli=args.output_file,
        output_file_preset=None,   # allow env/preset injection later if needed
        lang_cli=args.lang,
        custom_md_ext=args.extension,
        cover_path=Path(args.cover) if args.cover else None,
        epub2=args.epub2,
        skip_images=args.skip_images,
        keep_relative=args.keep_relative_paths,
        log_file=Path("export.log"),
    )
