import os
import shutil
import subprocess
import argparse
import yaml
import toml
from pathlib import Path
from scripts.enums.book_type import BookType

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define important directory and file paths
BOOK_DIR = "./manuscript"                       # Location of markdown files organized by sections
OUTPUT_DIR = "./output"                         # Output directory for compiled formats
BACKUP_DIR = "./output_backup"                  # Backup location for previous output
# Set to None to derive from pyproject.toml automatically.
# Set a string to override the output file base name manually.
OUTPUT_FILE = None
LOG_FILE = "export.log"                         # Log file for script and Pandoc output/errors

# Supporting script paths
SCRIPT_DIR = "./scripts"
ABSOLUTE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_absolute.py")     # Script to convert relative links to absolute
RELATIVE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_relative.py")     # Script to revert absolute links back to relative
IMG_SCRIPT = os.path.join(SCRIPT_DIR, "convert_img_tags.py")             # Script to modify image tag styles if needed

CONFIG_DIR = "./config"
METADATA_FILE =  Path(CONFIG_DIR) / "metadata.yaml"     # YAML file for Pandoc metadata (title, author, etc.)

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


def get_project_name_from_pyproject(pyproject_path="pyproject.toml"):
    """
    Extract the project name from the pyproject.toml file.

    This function reads the `[tool.poetry.name]` field from a pyproject.toml file
    and returns it as a string. This value is used as the base prefix for output filenames.

    Parameters:
    - pyproject_path (str): Path to the pyproject.toml file (default: "pyproject.toml")

    Returns:
    - str: The project name if found, otherwise a fallback value ("book")
    """
    try:
        data = toml.load(pyproject_path)
        return data["tool"]["poetry"]["name"]
    except Exception as e:
        print(f"⚠️ Could not read project name from pyproject.toml: {e}")
        return "book"


def get_metadata_language():
    """Read and return the 'lang' field from metadata.yaml if present, else return None"""
    if not METADATA_FILE.exists():
        print(f"⚠️ Metadata file not found at: {METADATA_FILE}")
        return None
    with METADATA_FILE.open("r", encoding="utf-8") as f:
        try:
            metadata = yaml.safe_load(f)
            return metadata.get("language")
        except yaml.YAMLError as e:
            print(f"⚠️ Failed to parse {METADATA_FILE}: {e}")
            return None


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
            f.write("title: 'CHANGE TO YOUR TITLE'\nauthor: 'YOUR NAME'\ndate: '2025'\nlang: 'en'\n") #TODO replace with your data


def compile_book(format, section_order, cover_path=None, force_epub2=False, lang="en", custom_ext=None):
    """
    Compiles the book into a specific format using Pandoc.

    Parameters:
    - format: Format to compile (e.g. pdf, docx)
    - section_order: Ordered list of sections to include
    """
    if format == "markdown":
        ext = custom_ext if custom_ext else "md"
    else:
        ext = FORMATS[format]
    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{ext}")

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
            "--metadata", f"lang={lang}"
        ])
        if force_epub2:
            pandoc_cmd.extend([
                "--metadata", "epub.version=2"
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
    parser.add_argument("--epub2", action="store_true", help="Force EPUB 2 export (for epubli compatibility).")
    parser.add_argument("--lang", type=str, help="Language code for metadata (e.g. en, de, fr)")
    parser.add_argument("--extension", type=str, help="Custom file extension for markdown export (default: md)")
    parser.add_argument(
        "--book-type",
        type=str,
        choices=[bt.value for bt in BookType],
        default=BookType.EBOOK.value,
        help="Specify the book type (ebook, paperback, etc.). Affects output file naming."
    )
    parser.add_argument("--output-file", type=str, help="Custom output file base name (overrides project name)")

    args = parser.parse_args()
    section_order = args.order.split(",")

    # Book type handling
    book_type = BookType(args.book_type)

    # Set global output filename
    global OUTPUT_FILE
    if args.output_file:
        OUTPUT_FILE = f"{args.output_file}-{book_type.value}"
    elif not OUTPUT_FILE:
        project_name = get_project_name_from_pyproject()
        OUTPUT_FILE = f"{project_name}-{book_type.value}"
    else:
        OUTPUT_FILE = f"{OUTPUT_FILE}-{book_type.value}"

    print(f"📘 Output file base name set to: {OUTPUT_FILE}")


    # Determine language: CLI > metadata.yaml > fallback
    metadata_lang = get_metadata_language()
    cli_lang = args.lang

    if cli_lang:
        if metadata_lang and cli_lang != metadata_lang:
            print("\n⚠️⚠️⚠️ LANGUAGE MISMATCH DETECTED ⚠️⚠️⚠️")
            print(f"Metadata file says: '{metadata_lang}' but CLI argument is: '{cli_lang}'")
            print("Using CLI argument value.\n")
        lang = cli_lang
    elif metadata_lang:
        lang = metadata_lang
        print(f"🌐 Using language from metadata.yaml: '{lang}'")
    else:
        lang = "en"
        print("⚠️ No language set in CLI or metadata.yaml. Defaulting to 'en'")

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
            compile_book(fmt, section_order, args.cover, args.epub2, lang, args.extension)
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
