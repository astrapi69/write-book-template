import subprocess
from pathlib import Path
import os

# Change working directory to project root (parent directory of scripts/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

SCRIPTS_DIR = Path("scripts")

EXPORT_FORMAT = "epub"         # You can change this to "pdf", "docx", etc.
BOOK_TYPE = "paperback"        # This will be passed to full_export_book.py


def run_script(script_name, *args):
    """
    Run a Python script with optional arguments.

    Parameters:
    - script_name (str): The name of the script to run (relative to SCRIPTS_DIR)
    - *args: Optional arguments passed to the script

    Returns:
    - bool: True if the script ran successfully, False otherwise
    """
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


def main():
    """
    Build the print-ready (paperback) version of the book.

    This script automates a series of steps:
    1. Strips internal links from the manuscript (for clean TOC and plain author pages)
    2. Converts any markdown links to plain text
    3. Runs the main export script to generate the EPUB (or other print-ready format)
    4. Reverts any modified files using `git restore .`

    Adjust the `steps` list if additional processing is needed before/after export.
    """
    print("📘 Building PRINT version of the book...\n")

    steps = [
        ("strip_links.py", []),  # Step 1: Clean TOC
        ("convert_links_to_plain_text.py", []),  # Step 2: Clean author section
        ("full_export_book.py", ["--format=" + EXPORT_FORMAT, "--book-type=" + BOOK_TYPE]), # Step 3: Build EPUB. You can change 'epub' to 'pdf', 'docx', etc.
    ]

    for script, args in steps:
        success = run_script(script, *args)
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
