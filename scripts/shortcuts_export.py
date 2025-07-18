"""
Shortcut utility for common book export operations.

📚 Usage (import in scripts or run via CLI):

    from shortcuts import export_epub, export_pdf, main

    # Run a shortcut directly
    export_pdf()

    # Or use CLI interface
    $ python shortcuts_export.py export_epub

🎯 Available shortcuts:
    - export_epub()
    - export_epub_with_cover()
    - export_pdf()
    - export_docx()
    - export_markdown()
    - export_print_version_epub()
    - all_formats_with_cover()
"""

import sys
import argparse
from scripts.full_export_book import main as export_main
from scripts.print_version_build import main as export_print_version_main

# --- Export Shortcuts ---

def export(format: str, cover: str = None):
    """
    Export book to the specified format using full-export pipeline

    :param format: One of 'pdf', 'epub', 'docx', 'markdown'
    :param cover: Optional path to cover image (used for EPUB)
    """
    sys.argv = ["full-export", f"--format={format}"]
    if cover:
        sys.argv.append(f"--cover={cover}")
    export_main()


def export_pdf():
    """Export book as PDF"""
    export("pdf")


def export_docx():
    """Export book as DOCX"""
    export("docx")


def export_epub():
    """Export book as EPUB (without cover)"""
    export("epub")


def export_markdown():
    """Export book as plain Markdown"""
    export("markdown")


def export_epub_with_cover():
    """Export EPUB with cover image"""
    export("epub", "./assets/covers/cover.jpg")


def export_print_version_epub():
    """Export the print-optimized EPUB version via print_version_build"""
    sys.argv = ["print-version-build", "--format=epub"]
    export_print_version_main()


def all_formats_with_cover():
    """Export all formats (PDF, EPUB, DOCX) with EPUB cover"""
    sys.argv = [
        "full-export",
        "--format=pdf,epub,docx",
        "--cover=./assets/covers/cover.jpg"
    ]
    export_main()


# --- CLI Dispatcher ---

available_shortcuts = {
    "export_epub": export_epub,
    "export_epub_with_cover": export_epub_with_cover,
    "export_pdf": export_pdf,
    "export_docx": export_docx,
    "export_markdown": export_markdown,
    "export_print_version_epub": export_print_version_epub,
    "all_formats_with_cover": all_formats_with_cover,
}

def main():
    """Main CLI dispatcher for shortcuts"""
    parser = argparse.ArgumentParser(
        description="📚 Book Project Shortcut Runner",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\nRun a shortcut like: poetry run shortcuts export_pdf"
    )

    shortcut_names = sorted(available_shortcuts.keys())
    shortcut_help = "\n".join([f"  {name}" for name in shortcut_names])

    parser.add_argument(
        "task",
        nargs="?",
        choices=shortcut_names,
        help=f"Available shortcuts:\n{shortcut_help}"
    )

    args = parser.parse_args()

    if args.task:
        available_shortcuts[args.task]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
