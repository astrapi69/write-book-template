import subprocess
from pathlib import Path
import os
import argparse

# Allowed book types
VALID_BOOK_TYPES = ["paperback", "hardcover"]
DEFAULT_BOOK_TYPE = "paperback"

# Change working directory to project root (parent directory of scripts/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

SCRIPTS_DIR = Path("scripts")


def run_script(script_name, *args):
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    try:
        subprocess.run(["python3", str(script_path), *args], check=True)
        print(f"✅ Ran: {script_name} {' '.join(args) if args else ''}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def parse_args():
    parser = argparse.ArgumentParser(description="Build a print-ready version of the book.")
    parser.add_argument(
        "--book-type",
        default=DEFAULT_BOOK_TYPE,
        help=f"Specify the book type (default: {DEFAULT_BOOK_TYPE})"
    )
    args = parser.parse_args()

    # Validate book type manually
    book_type = args.book_type.lower()
    if book_type not in VALID_BOOK_TYPES:
        print(f"⚠️ Invalid book type '{args.book_type}' provided. Falling back to default: '{DEFAULT_BOOK_TYPE}'")
        book_type = DEFAULT_BOOK_TYPE

    return book_type


def main():
    book_type = parse_args()
    export_format = "epub"

    print(f"📘 Building PRINT version of the book ({book_type.upper()})...\n")

    steps = [
        ("strip_links.py", []),
        ("convert_links_to_plain_text.py", []),
        ("full_export_book.py", [f"--format={export_format}", f"--book-type={book_type}"]),
    ]

    for script, arguments in steps:
        success = run_script(script, *arguments)
        if not success:
            print("🛑 Build process aborted.")
            return

    print("\n🎉 Print version EPUB successfully generated!")
    print("\n🔄 Reverting modified files to original state...")
    try:
        subprocess.run(["git", "restore", "."], check=True)
        print("✅ Reverted all changes using git restore")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to revert changes: {e}")


if __name__ == "__main__":
    main()
