import subprocess
from pathlib import Path
import os

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
        print(f"✅ Ran: {script_name} {' '.join(args)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def main():
    print("📘 Building PRINT version of the book...\n")

    steps = [
        ("strip_links.py", []),  # Step 1: Clean TOC
        ("convert_links_to_plain_text.py", []),  # Step 2: Clean author section
        ("full_export_book.py", ["--format=epub"]),  # Step 3: Build EPUB. You can change 'epub' to 'pdf', 'docx', etc.
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
