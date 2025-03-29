import os
import shutil
import subprocess
import argparse

# Change working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define key paths and constants
BOOK_DIR = "./manuscript"
OUTPUT_DIR = "./output"
BACKUP_DIR = "./output_backup"
OUTPUT_FILE = "book"  # ✅ You can change this to your book's name
METADATA_FILE = "config/metadata.yaml"
LOG_FILE = "export.log"

# Script paths
SCRIPT_DIR = "./scripts"
ABSOLUTE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_absolute.py")
RELATIVE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_relative.py")
IMG_SCRIPT = os.path.join(SCRIPT_DIR, "convert_img_tags.py")

# Output formats
FORMATS = {
    "markdown": "gfm",
    "pdf": "pdf",
    "epub": "epub",
    "docx": "docx",
}

# Default section order (customizable)
DEFAULT_SECTION_ORDER = [
    "front-matter/toc.md",
    "front-matter/preface.md",
    "front-matter/introduction.md",
    "front-matter/foreword.md",
    "chapters",
    "back-matter/epilogue.md",
    "back-matter/glossary.md",
    "back-matter/appendix.md",
    "back-matter/acknowledgments.md",
    "back-matter/about-the-author.md",
    "back-matter/faq.md",
    "back-matter/bibliography.md",
    "back-matter/index.md",
]

def run_script(script_path, arg=None):
    """Run a Python script with optional arguments and log output."""
    try:
        cmd = ["python3", script_path]
        if arg:
            cmd.append(arg)
        subprocess.run(cmd, check=True, stdout=open(LOG_FILE, "a"), stderr=open(LOG_FILE, "a"))
        print(f"✅ Successfully executed: {script_path} {arg if arg else ''}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running script {script_path}: {e}")
        raise  # <--- This is needed so tests detect the failure!

def prepare_output_folder():
    """ Ensure output folder exists and backup old output """
    os.makedirs(OUTPUT_DIR, exist_ok=True)  # ✅ Always create the output folder
    os.makedirs(BACKUP_DIR, exist_ok=True)  # ✅ Ensure backup folder exists

    if os.path.exists(OUTPUT_DIR) and os.listdir(OUTPUT_DIR):  # ✅ Only back up if there are files
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)  # Remove old backup
        shutil.move(OUTPUT_DIR, BACKUP_DIR)  # Move current output to backup

def ensure_metadata_file():
    """Ensure metadata.yaml exists to avoid Pandoc warnings."""
    if not os.path.exists(METADATA_FILE):
        print(f"⚠️ Metadata file missing! Creating default {METADATA_FILE}.")
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            f.write("title: 'AI for Everyone'\nauthor: 'Your Name'\ndate: '2025'\n")

def compile_book(format, section_order):
    """Compile book using Pandoc into the given format."""
    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{FORMATS[format]}")
    md_files = []

    # Assemble markdown files in the specified order
    for section in section_order:
        section_path = os.path.join(BOOK_DIR, section)
        if os.path.isdir(section_path):
            md_files.extend(
                sorted(os.path.join(section_path, f) for f in os.listdir(section_path) if f.endswith(".md"))
            )
        elif os.path.isfile(section_path):
            md_files.append(section_path)

    if not md_files:
        print(f"❌ No Markdown files found for format {format}. Skipping.")
        return

    pandoc_cmd = [
                     "pandoc",
                     "--from=markdown",
                     f"--to={FORMATS[format]}",
                     f"--output={output_path}",
                     f"--resource-path={os.path.abspath('./assets')}",
                     f"--metadata-file={METADATA_FILE}",
                 ] + md_files

    if format == "pdf":
        pandoc_cmd.append("--pdf-engine=xelatex")  # More font-friendly than pdflatex

    try:
        with open(LOG_FILE, "a") as log_file:
            subprocess.run(pandoc_cmd, check=True, stdout=log_file, stderr=log_file)
        print(f"✅ Successfully generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compiling {format}: {e}")

def main():
    """Main script execution logic."""
    parser = argparse.ArgumentParser(description="Export your book into multiple formats.")
    parser.add_argument("--skip-images", action="store_true", help="Skip image conversion scripts.")
    parser.add_argument("--format", type=str, help="Specify formats (comma-separated: pdf,epub,docx,markdown).")
    parser.add_argument("--order", type=str, default=",".join(DEFAULT_SECTION_ORDER), help="Specify document order.")

    args = parser.parse_args()
    section_order = args.order.split(",")

    # Step 1: Convert image paths to absolute
    if not args.skip_images:
        run_script(ABSOLUTE_SCRIPT)
        run_script(IMG_SCRIPT, "--to-absolute")

    # Step 2: Prepare environment
    prepare_output_folder()
    ensure_metadata_file()

    # Step 3: Compile book in requested formats
    selected_formats = args.format.split(",") if args.format else FORMATS.keys()
    for fmt in selected_formats:
        if fmt in FORMATS:
            compile_book(fmt, section_order)
        else:
            print(f"⚠️ Skipping unknown format: {fmt}")

    # Step 4: Restore original image paths
    if not args.skip_images:
        run_script(RELATIVE_SCRIPT)
        run_script(IMG_SCRIPT, "--to-relative")

    print("🎉 All formats generated successfully! Check export.log for details.")

if __name__ == "__main__":
    main()
