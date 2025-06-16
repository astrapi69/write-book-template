import os
import shutil
import subprocess
import argparse

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define important directory and file paths
BOOK_DIR = "./manuscript"                       # Location of markdown files organized by sections
OUTPUT_DIR = "./output"                         # Output directory for compiled formats
BACKUP_DIR = "./output_backup"                  # Backup location for previous output
OUTPUT_FILE = "book"                            # Base name for the output files #TODO replace with your data
METADATA_FILE = "config/metadata.yaml"          # YAML file for Pandoc metadata (title, author, etc.)
LOG_FILE = "export.log"                         # Log file for script and Pandoc output/errors

# Paths to supporting scripts
SCRIPT_DIR = "./scripts"
ABSOLUTE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_absolute.py")     # Script to convert relative links to absolute
RELATIVE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_relative.py")     # Script to revert absolute links back to relative
IMG_SCRIPT = os.path.join(SCRIPT_DIR, "convert_img_tags.py")             # Script to modify image tag styles if needed

# Supported output formats and their corresponding Pandoc targets
FORMATS = {
    "markdown": "gfm",  # GitHub-Flavored Markdown
    "pdf": "pdf",       # PDF format
    "epub": "epub",     # EPUB eBook format
    "docx": "docx",     # Microsoft Word format
}

# Default section order (customizable)
DEFAULT_SECTION_ORDER = [
    "front-matter/toc.md",
    "front-matter/preface.md",
    "front-matter/introduction.md",
    "front-matter/foreword.md",
    "chapters",  # Entire chapters folder
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


def prepare_output_folder(verbose=False):
    """
    Prepares the output directory by ensuring it's empty.
    - Deletes existing backup dir if present
    - Moves current output dir to backup
    - Creates a fresh output dir
    """
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
        if verbose:
            print("📦 Deleted old backup directory.")

    if os.path.exists(OUTPUT_DIR) and os.listdir(OUTPUT_DIR):
        shutil.move(OUTPUT_DIR, BACKUP_DIR)
        if verbose:
            print("📁 Moved current output to backup directory.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if verbose:
        print("📂 Created clean output directory.")


def ensure_metadata_file():
    """
    Ensures the metadata file exists.
    - Prevents Pandoc warnings by providing minimal metadata if missing.
    """
    if not os.path.exists(METADATA_FILE):
        print(f"⚠️ Metadata file missing! Creating default {METADATA_FILE}.")
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            f.write("title: 'CHANGE TO YOUR TITLE'\nauthor: 'YOUR NAME'\ndate: '2025'\n") #TODO replace with your data


def compile_book(format, section_order, cover_path=None):
    """
    Compiles the book into a specific format using Pandoc.

    Parameters:
    - format: Format to compile (e.g. pdf, docx)
    - section_order: Ordered list of sections to include
    """
    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{FORMATS[format]}")
    md_files = []

    # Gather markdown files from the specified order
    for section in section_order:
        section_path = os.path.join(BOOK_DIR, section)
        if os.path.isdir(section_path):
            # Include all .md files in directory, sorted
            md_files.extend(
                sorted(os.path.join(section_path, f) for f in os.listdir(section_path) if f.endswith(".md"))
            )
        elif os.path.isfile(section_path):
            # Include specific markdown file
            md_files.append(section_path)

    if not md_files:
        print(f"❌ No Markdown files found for format {format}. Skipping.")
        return

    # Construct Pandoc command
    pandoc_cmd = [
                     "pandoc",
                     "--verbose",
                     "--from=markdown",
                     f"--to={FORMATS[format]}",
                     f"--output={output_path}",
                     f"--resource-path={os.path.abspath('./assets')}",  # To resolve images and assets
                     f"--metadata-file={METADATA_FILE}",
                 ] + md_files  # Append all markdown files to compile

    if format == "epub":
        pandoc_cmd.extend([
            "--metadata", "lang=en"
        ])
        if cover_path:
            pandoc_cmd.append(f"--epub-cover-image={cover_path}")

    # For PDF output, specify the PDF engine and font options
    if format == "pdf":
        pandoc_cmd.extend([
            "--pdf-engine=lualatex",  # xelatex, lualatex, pdflatex
            "-V", "mainfont=DejaVu Sans",
            "-V", "monofont=DejaVu Sans Mono"
        ])

    # For Markdown output: prevent line breaks in links and paragraphs
    if format == "markdown":
        pandoc_cmd.append("--wrap=none")

    # Run Pandoc and log output
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
    parser.add_argument("--format", type=str, help="Specify formats (comma-separated, e.g., pdf,epub).")
    parser.add_argument("--order", type=str, default=",".join(DEFAULT_SECTION_ORDER),
                        help="Specify document order (comma-separated).")
    parser.add_argument("--cover", type=str, help="Optional path to cover image (for EPUB export).")


    args = parser.parse_args()
    section_order = args.order.split(",")

    # Step 1: Convert image paths to absolute
    # Run pre-processing scripts unless user opts out
    if not args.skip_images:
        run_script(ABSOLUTE_SCRIPT)                      # Convert relative paths to absolute
        run_script(IMG_SCRIPT, "--to-absolute")     # Process image tags

    # Step 2: Prepare environment
    prepare_output_folder()                              # Prepare folders and backup if needed
    ensure_metadata_file()                               # Make sure metadata exists

    # Step 3: Compile book in requested formats
    # Determine formats to export
    selected_formats = args.format.split(",") if args.format else FORMATS.keys()

    # Compile the book for each format
    for fmt in selected_formats:
        if fmt in FORMATS:
            compile_book(fmt, section_order, args.cover)
        else:
            print(f"⚠️ Skipping unknown format: {fmt}")

    # Step 4: Restore original image paths
    # Revert any image/URL changes made before compilation
    if not args.skip_images:
        run_script(RELATIVE_SCRIPT)                      # Convert absolute paths back to relative
        run_script(IMG_SCRIPT, "--to-relative")     # Revert image tag changes

    print("🎉 All formats generated successfully! Check export.log for details.")


# Entry point
if __name__ == "__main__":
    main()
