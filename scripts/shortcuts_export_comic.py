# scripts/shortcuts_export_comic.py
"""
Shortcut utility for common comic book export operations.

📚 Usage (import in scripts or run via CLI):

    from shortcuts_export_comic import export_comic_pdf, export_comic_html, main

    # Run a shortcut directly
    export_comic_pdf()

    # Or use CLI interface
    $ poetry run export-comic-shortcuts export_comic_pdf

🎯 Available shortcuts:
    - export_comic_html()
    - export_comic_pdf()
    - export_comic_markdown()   ← not yet implemented
"""

import sys
import argparse
from scripts.full_export_comic import main as export_comic_main

# --- Export Shortcuts ---


def export_comic_html():
    sys.argv = [
        "export-comic",
        # no extra flags = HTML only
    ]
    export_comic_main()


def export_comic_pdf():
    sys.argv = ["export-comic", "--pdf"]
    export_comic_main()


def export_comic_markdown():
    print("⚠️ Markdown export is not implemented for comics yet.")
    # You could later map this to pandoc or HTML→markdown if desired.


# --- CLI Dispatcher ---

available_shortcuts = {
    "export_comic_html": export_comic_html,
    "export_comic_pdf": export_comic_pdf,
    "export_comic_markdown": export_comic_markdown,
}


def main():
    """Main CLI dispatcher for comic export shortcuts"""
    parser = argparse.ArgumentParser(
        description="📚 Comic Book Project Shortcut Runner",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\nRun a shortcut like: poetry run export-comic-shortcuts export_comic_pdf",
    )

    shortcut_names = sorted(available_shortcuts.keys())
    shortcut_help = "\n".join([f"  {name}" for name in shortcut_names])

    parser.add_argument(
        "task",
        nargs="?",
        choices=shortcut_names,
        help=f"Available shortcuts:\n{shortcut_help}",
    )

    args = parser.parse_args()

    if args.task:
        available_shortcuts[args.task]()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
