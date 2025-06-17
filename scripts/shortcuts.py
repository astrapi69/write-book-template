"""
Shortcut utility for common book export operations.

You can import this file to call quick actions like:
- export_epub()
- export_markdown()
- export_epub_with_cover()
Or run it directly via CLI:
> python shortcuts.py export_epub
"""

import sys
from scripts.full_export_book import main as export_main
from scripts.print_version_build import main as export_print_version_main


def export(format: str, cover: str = None):
    """
    General export shortcut with optional cover image

    :param format: Format to export, e.g., 'epub', 'pdf', 'markdown', 'docx'
    :param cover: Optional path to cover image (for EPUB)
    """
    sys.argv = ["full-export", f"--format={format}"]
    if cover:
        sys.argv.append(f"--cover={cover}")
    export_main()


def export_epub():
    """
    Shortcut: Export only the EPUB version of the book
    """
    export("epub")


def export_markdown():
    """
    Shortcut: Export only the Markdown version of the book
    """
    export("markdown")


def export_epub_with_cover():
    """
    Shortcut: Export EPUB version with a cover image
    """
    export("epub", "./assets/covers/cover.jpg")


def export_print_version_epub():
    """
    Shortcut: Generate the print-version EPUB via print_version_build pipeline
    """
    sys.argv = ["print-version-build", "--format=epub"]
    export_print_version_main()


def all_formats_with_cover():
    """
    Shortcut: Export all supported formats (PDF, EPUB, DOCX) with a cover for EPUB
    """
    sys.argv = [
        "full-export",
        "--format=pdf,epub,docx",
        "--cover=./assets/covers/cover.jpg"
    ]
    export_main()


# Optional CLI usage
if __name__ == "__main__":
    import argparse

    available_shortcuts = {
        "export_epub": export_epub,
        "export_markdown": export_markdown,
        "export_epub_with_cover": export_epub_with_cover,
        "export_print_version_epub": export_print_version_epub,
        "all_formats_with_cover": all_formats_with_cover,
    }

    parser = argparse.ArgumentParser(description="Run export shortcuts.")
    parser.add_argument("task", choices=available_shortcuts.keys(), help="Shortcut name to run")
    args = parser.parse_args()

    # Call the selected shortcut
    available_shortcuts[args.task]()
