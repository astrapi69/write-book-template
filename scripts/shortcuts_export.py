# scripts/shortcuts_export.py
"""
Shortcut utility for common book export operations.

📚 Usage (import in scripts or run via CLI):

    from shortcuts import export_epub, export_pdf, main

    # Run a shortcut directly
    export_pdf()

    # Or use CLI interface (now with passthrough args):
    $ python scripts/shortcuts_export.py export_pdf --skip-images --keep-relative-paths
    $ poetry run shortcuts export_epub --cover=./assets/covers/custom.jpg

🎯 Available shortcuts:
    - export_epub()
    - export_epub_with_cover()
    - export_epub2()
    - export_epub2_with_cover()
    - export_pdf()
    - export_docx()
    - export_markdown()
    - export_print_version_epub()
    - export_print_version_paperback(),
    - export_print_version_hardcover(),
    - all_formats_with_cover()
"""

import sys
import argparse
from typing import Iterable, List

from scripts.full_export_book import main as export_main
from scripts.print_version_build import main as export_print_version_main

# --- Helpers -----------------------------------------------------------------

def _has_option(extra: Iterable[str], name: str) -> bool:
    """Return True if --name or --name=... is present in extra args."""
    name_eq = name + "="
    extra = list(extra)
    for i, tok in enumerate(extra):
        if tok == name:
            return True
        if tok.startswith(name_eq):
            return True
        # Also handle separated value form: --name value
        if tok == name and i + 1 < len(extra):
            return True
    return False


def _run_full_export(args_list: List[str]):
    """Invoke the full export pipeline with a synthetic argv."""
    sys.argv = ["full-export", *args_list]
    export_main()


def _run_print_version(args_list: List[str]):
    """Invoke the print-version pipeline with a synthetic argv."""
    sys.argv = ["print-version-build", *args_list]
    export_print_version_main()

# --- Export Shortcuts ---------------------------------------------------------

def export(format: str, cover: str | None = None, *extra: str):
    """
    Export book to the specified format using full-export pipeline.
    - Adds --format=FORMAT unless user already provided --format
    - Adds --cover=... unless user already provided --cover
    """
    extra = list(extra)
    args: List[str] = []

    # Only add --format if not already provided by the user
    if not _has_option(extra, "--format"):
        args.append(f"--format={format}")

    # Only add --cover if not already provided by the user and a default is given
    if cover and not _has_option(extra, "--cover"):
        args.append(f"--cover={cover}")

    args.extend(extra)
    _run_full_export(args)


def export_pdf(*extra: str):
    """Export book as PDF"""
    export("pdf", None, *extra)


def export_docx(*extra: str):
    """Export book as DOCX"""
    export("docx", None, *extra)


def export_epub(*extra: str):
    """Export book as EPUB (without cover by default)"""
    export("epub", None, *extra)


def export_markdown(*extra: str):
    """Export book as plain Markdown"""
    export("markdown", None, *extra)


def export_epub_with_cover(*extra: str):
    """Export EPUB with cover image (can be overridden by --cover=...)"""
    export("epub", "./assets/covers/cover.jpg", *extra)


def all_formats_with_cover(*extra: str):
    """Export all formats (PDF, EPUB, DOCX) with EPUB cover"""
    extra = list(extra)
    args: List[str] = []
    if not _has_option(extra, "--format"):
        args.append("--format=pdf,epub,docx")
    if not _has_option(extra, "--cover"):
        args.append("--cover=./assets/covers/cover.jpg")
    args.extend(extra)
    _run_full_export(args)


def export_epub2(*extra: str):
    """Export EPUB in EPUB 2 format (adds --epub2 unless user passed it)"""
    extra = list(extra)
    args: List[str] = []
    if not _has_option(extra, "--format"):
        args.append("--format=epub")
    # Add --epub2 only if user didn't specify
    if not _has_option(extra, "--epub2"):
        args.append("--epub2")
    args.extend(extra)
    _run_full_export(args)


def export_epub2_with_cover(*extra: str):
    """Export EPUB 2 with cover image (respects user overrides)"""
    extra = list(extra)
    args: List[str] = []
    if not _has_option(extra, "--format"):
        args.append("--format=epub")
    if not _has_option(extra, "--epub2"):
        args.append("--epub2")
    if not _has_option(extra, "--cover"):
        args.append("--cover=./assets/covers/cover.jpg")
    args.extend(extra)
    _run_full_export(args)


def export_print_version_epub(*extra: str):
    """Export the print-optimized EPUB via print_version_build"""
    _run_print_version(list(extra))


def export_print_version_paperback(*extra: str):
    """Export print-optimized EPUB for paperback"""
    extra = list(extra)
    args: List[str] = []
    if not _has_option(extra, "--book-type"):
        args.append("--book-type=paperback")
    args.extend(extra)
    _run_print_version(args)


def export_print_version_hardcover(*extra: str):
    """Export print-optimized EPUB for hardcover"""
    extra = list(extra)
    args: List[str] = []
    if not _has_option(extra, "--book-type"):
        args.append("--book-type=hardcover")
    args.extend(extra)
    _run_print_version(args)


def export_safe(format: str, *extra: str):
    """
    Export book in safe mode:
    - Always adds --skip-images and --keep-relative-paths
    - Skips Step 1 and Step 4 in full_export_book (no in-place file edits)

    :param format: One of 'pdf', 'epub', 'docx', 'markdown'
    """
    extra = list(extra)
    args: list[str] = []

    # Add format unless user already specified
    if not _has_option(extra, "--format"):
        args.append(f"--format={format}")

    # Force safe flags unless user overrides them
    if not _has_option(extra, "--skip-images"):
        args.append("--skip-images")


    args.extend(extra)
    _run_full_export(args)


def export_pdf_safe(*extra: str):
    """Export book as PDF (safe mode)"""
    export_safe("pdf", *extra)


def export_epub_safe(*extra: str):
    """Export book as EPUB (safe mode)"""
    export_safe("epub", *extra)


def export_docx_safe(*extra: str):
    """Export book as DOCX (safe mode)"""
    export_safe("docx", *extra)


def export_markdown_safe(*extra: str):
    """Export book as Markdown (safe mode)"""
    export_safe("markdown", *extra)

# --- CLI Dispatcher -----------------------------------------------------------

available_shortcuts = {
    "export_epub": export_epub,
    "export_epub_with_cover": export_epub_with_cover,
    "export_epub2": export_epub2,
    "export_epub2_with_cover": export_epub2_with_cover,
    "export_pdf": export_pdf,
    "export_docx": export_docx,
    "export_markdown": export_markdown,
    "export_print_version_epub": export_print_version_epub,
    "export_print_version_paperback": export_print_version_paperback,
    "export_print_version_hardcover": export_print_version_hardcover,
    "all_formats_with_cover": all_formats_with_cover,
    "export_pdf_safe": export_pdf_safe,
    "export_epub_safe": export_epub_safe,
    "export_docx_safe": export_docx_safe,
    "export_markdown_safe": export_markdown_safe,
}

def main():
    """Main CLI dispatcher for shortcuts (supports passthrough args)"""
    parser = argparse.ArgumentParser(
        description="📚 Book Project Shortcut Runner",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "\nExamples:\n"
            "  poetry run shortcuts export_pdf --skip-images --keep-relative-paths\n"
            "  poetry run shortcuts export_epub --cover=./assets/covers/custom.jpg\n"
            "  poetry run shortcuts export_epub2 --output-file=mybook --skip-images\n"
            "  poetry run shortcuts export_print_version_paperback --toc-depth=2\n"
        ),
    )

    shortcut_names = sorted(available_shortcuts.keys())
    shortcut_help = "\n".join([f"  {name}" for name in shortcut_names])

    parser.add_argument(
        "task",
        nargs="?",
        choices=shortcut_names,
        help=f"Available shortcuts:\n{shortcut_help}"
    )

    # Parse known args and keep the rest to pass through
    args, extra = parser.parse_known_args()

    if args.task:
        # Call the chosen shortcut with passthrough args
        available_shortcuts[args.task](*extra)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()