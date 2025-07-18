"""
Shortcut utility for common init operations.

📚 Usage (import in scripts or run via CLI):

    from shortcuts import run_update_metadata_values, run_init_book_project

    # Run a shortcut directly
    export_pdf()

    # Or use CLI interface
    $ python shortcuts_export.py run_update_metadata_values

🎯 Available shortcuts:
    - run_update_metadata_values()
    - run_init_book_project()
"""

import argparse
from scripts.update_metadata_values import main as update_metadata_values_main
from scripts.init_book_project import main as init_book_project_main


# --- Initialization Shortcuts ---

def run_init_book_project():
    """Initialize a new book project structure"""
    init_book_project_main()


def run_update_metadata_values():
    """Update metadata.yaml using preset values"""
    update_metadata_values_main()


# --- CLI Dispatcher ---

available_shortcuts = {
    "run_update_metadata_values": run_update_metadata_values,
    "run_init_book_project": run_init_book_project,
}

def main():
    """Main CLI dispatcher for shortcuts"""
    parser = argparse.ArgumentParser(
        description="📚 Book Project Shortcut Runner",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="\nRun a shortcut like: poetry run shortcuts run_init_book_project"
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
