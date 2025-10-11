# scripts/full_export_book.py
import os
import shutil
import subprocess
import argparse
import yaml
import toml
import threading
import tempfile
from pathlib import Path
from scripts.enums.book_type import BookType
from scripts.validate_format import (
    validate_epub_with_epubcheck,
    validate_pdf,
    validate_markdown,
    validate_docx,
)

# replace with your data
DEFAULT_METADATA = """title: 'CHANGE TO YOUR TITLE'
author: 'YOUR NAME'
date: '2025'
lang: 'en'
"""

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define important directory and file paths
BOOK_DIR = "./manuscript"  # Location of markdown files organized by sections
OUTPUT_DIR = "./output"  # Output directory for compiled formats
BACKUP_DIR = "./output_backup"  # Backup location for previous output
# Set to None to derive from pyproject.toml automatically.
# Set a string to override the output file base name manually.
OUTPUT_FILE = ""
LOG_FILE = "export.log"  # Log file for script and Pandoc output/errors

# Supporting script paths
SCRIPT_DIR = "./scripts"
ABSOLUTE_SCRIPT = os.path.join(
    SCRIPT_DIR, "convert_to_absolute.py"
)  # Script to convert relative links to absolute
RELATIVE_SCRIPT = os.path.join(
    SCRIPT_DIR, "convert_to_relative.py"
)  # Script to revert absolute links back to relative
IMG_SCRIPT = os.path.join(
    SCRIPT_DIR, "convert_img_tags.py"
)  # Script to modify image tag styles if needed
TOC_FILE = Path(BOOK_DIR) / "front-matter" / "toc.md"
NORMALIZE_TOC = os.path.join(SCRIPT_DIR, "normalize_toc_links.py")

CONFIG_DIR = "./config"
METADATA_FILE = (
    Path(CONFIG_DIR) / "metadata.yaml"
)  # YAML file for Pandoc metadata (title, author, etc.)

# Supported output formats and their corresponding Pandoc targets
FORMATS = {
    "markdown": "gfm",  # GitHub-Flavored Markdown
    "pdf": "pdf",  # PDF format
    "epub": "epub",  # EPUB eBook format
    "docx": "docx",  # Microsoft Word format
}

# Default section order (customizable)
DEFAULT_SECTION_ORDER = [
    "front-matter/imprint.md",
    "front-matter/toc.md",
    "front-matter/preface.md",
    "front-matter/foreword.md",
    "chapters",  # Entire chapters folder
    "back-matter/epilogue.md",
    "back-matter/glossary.md",
    "back-matter/appendix.md",
    "back-matter/acknowledgments.md",
    "back-matter/about-the-author.md",
    "back-matter/bibliography.md",
]

# New: explicit orders per product
# ebook section order
EBOOK_SECTION_ORDER = DEFAULT_SECTION_ORDER
# Paperback section order (customizable)
PAPERBACK_SECTION_ORDER = [
    "front-matter/imprint.md",
    "front-matter/toc_print_edition.md",  # <-- print ToC with page numbers
    "front-matter/preface.md",
    "front-matter/foreword.md",
    "chapters",  # Entire chapters folder
    "back-matter/epilogue.md",
    "back-matter/glossary.md",
    "back-matter/appendix.md",
    "back-matter/acknowledgments.md",
    "back-matter/about-the-author.md",
    "back-matter/bibliography.md",
]

# Hardcover section order (customizable)
HARDCOVER_SECTION_ORDER = PAPERBACK_SECTION_ORDER


def pick_section_order(book_type: "BookType", fmt: str) -> list[str]:
    """
    Decide which section order to use if --order was not provided.
    - ebook  -> EBOOK_SECTION_ORDER
    - paperback/hardcover -> PAPERBACK/HARDCOVER_SECTION_ORDER
    Note: For non-EPUB builds of ebook (e.g., markdown or pdf drafts), we still
    stick to EBOOK_SECTION_ORDER unless user overrides.
    """
    if book_type.value == "ebook":
        return EBOOK_SECTION_ORDER
    if book_type.value == "paperback":
        return PAPERBACK_SECTION_ORDER
    if book_type.value == "hardcover":
        return HARDCOVER_SECTION_ORDER
    # fallback
    return DEFAULT_SECTION_ORDER


def resolve_ext(fmt: str, custom_markdown_ext: str | None) -> str:
    if fmt == "markdown":
        return custom_markdown_ext if custom_markdown_ext else "md"
    return FORMATS[fmt]


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
    if pyproject_path is None:
        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        data = toml.load(pyproject_path)
        return (
            data.get("tool", {}).get("poetry", {}).get("name")
            or data.get("project", {}).get("name")
            or "book"
        )
    except Exception as e:
        print(f"⚠️ Could not read project name from {pyproject_path}: {e}")
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
        subprocess.run(
            cmd, check=True, stdout=open(LOG_FILE, "a"), stderr=open(LOG_FILE, "a")
        )
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


def get_or_create_metadata_file(preferred_path: Path | str | None = None):
    """
    Return a usable metadata file path.

    - If the preferred_path exists, return it with `is_temp=False`.
    - Otherwise, create a temporary metadata YAML file with default content
      and return it with `is_temp=True`.
    """
    path = Path(preferred_path) if preferred_path else METADATA_FILE
    if path.exists():
        return path, False

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    tmp.write(DEFAULT_METADATA.encode("utf-8"))
    tmp.flush()
    tmp.close()
    return Path(tmp.name), True


def ensure_metadata_file():
    """
    Ensures the metadata file exists.
    - Prevents Pandoc warnings by providing minimal metadata if missing.
    """
    if not os.path.exists(METADATA_FILE):
        print(f"⚠️ Metadata file missing! Creating default {METADATA_FILE}.")
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            # TODO replace with your data
            f.write(
                'title: "CHANGE TO YOUR TITLE"\n'
                'author: "YOUR NAME"\n'
                'date: "2025"\n'
                'lang: "en"\n'
            )


def compile_book(
    format,
    section_order,
    cover_path=None,
    force_epub2=False,
    lang="en",
    custom_ext=None,
):
    """
    Compiles the book into a specific format using Pandoc.

    Parameters:
    - format: Format to compile (e.g. pdf, docx)
    - section_order: Ordered list of sections to include
    """
    ext = resolve_ext(format, custom_ext)
    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{ext}")

    md_files = []

    # Gather markdown files from the specified order
    for section in section_order:
        section_path = os.path.join(BOOK_DIR, section)
        if os.path.isdir(section_path):
            # Include all .md files in directory, sorted
            md_files.extend(
                sorted(
                    os.path.join(section_path, f)
                    for f in os.listdir(section_path)
                    if f.endswith(".md")
                )
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
        pandoc_cmd.extend(["--metadata", f"lang={lang}"])
        if force_epub2:
            pandoc_cmd.extend(["--metadata", "epub.version=2"])
        if cover_path:
            pandoc_cmd.append(f"--epub-cover-image={cover_path}")

    # For PDF output, specify the PDF engine and font options
    if format == "pdf":
        pandoc_cmd.extend(
            [
                "--pdf-engine=lualatex",  # xelatex, lualatex, pdflatex
                "-V",
                "mainfont=DejaVu Sans",
                "-V",
                "monofont=DejaVu Sans Mono",
            ]
        )

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


# Step 1a: Normalize TOC (only if it's the web/ebook ToC 'toc.md')
def normalize_toc_if_needed(toc_path: Path, args):
    try:
        if toc_path.exists() and toc_path.name == "toc.md":
            toc_mode = "strip-to-anchors"
            toc_ext = args.extension if args.extension else "md"
            subprocess.run(
                [
                    "python3",
                    NORMALIZE_TOC,
                    "--toc",
                    str(toc_path),
                    "--mode",
                    toc_mode,
                    "--ext",
                    toc_ext,
                ],
                check=True,
                stdout=open(LOG_FILE, "a"),
                stderr=open(LOG_FILE, "a"),
            )
            print(f"✅ TOC normalized using mode={toc_mode}: {toc_path}")
        else:
            print(f"ℹ️  Skipping TOC normalization for {toc_path.name} (not ebook toc).")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error normalizing TOC: {e}")


def main():
    """Main script execution logic."""
    parser = argparse.ArgumentParser(
        description="Export your book into multiple formats."
    )
    parser.add_argument(
        "--format", type=str, help="Specify formats (comma-separated, e.g., pdf,epub)."
    )
    parser.add_argument(
        "--order",
        type=str,
        default=None,  # was: ",".join(DEFAULT_SECTION_ORDER)
        help="Specify document order (comma-separated). If omitted, a sane default is chosen based on --book-type.",
    )

    parser.add_argument(
        "--cover", type=str, help="Optional path to cover image (for EPUB export)."
    )
    parser.add_argument(
        "--epub2",
        action="store_true",
        help="Force EPUB 2 export (for epubli compatibility).",
    )
    parser.add_argument(
        "--lang", type=str, help="Language code for metadata (e.g. en, de, fr)"
    )
    parser.add_argument(
        "--extension",
        type=str,
        help="Custom file extension for markdown export (default: md)",
    )
    parser.add_argument(
        "--book-type",
        type=str,
        choices=[bt.value for bt in BookType],
        default=BookType.EBOOK.value,
        help="Specify the book type (ebook, paperback, etc.). Affects output file naming.",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Custom output file base name (overrides project name)",
    )
    parser.add_argument(
        "--no-type-suffix",
        action="store_true",
        help="Do not append '-{book_type}' to the output base name.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip all image-related steps (no path rewrites, no tag transforms).",
    )
    group.add_argument(
        "--keep-relative-paths",
        action="store_true",
        help="Do not rewrite image/URL paths to absolute and back; keeps relative paths (skips Steps 1 and 4).",
    )

    args = parser.parse_args()

    # Book type handling
    book_type = BookType(args.book_type)
    # Decide section order: CLI > auto by book type
    if args.order:
        section_order = args.order.split(",")
    else:
        # we don’t know the format yet (could be multiple), so we pass a callable down
        # and re-pick per format later, OR pick a single order now:
        # We’ll pick later per format to allow mixed builds like: --format=epub,pdf
        section_order = None

    # Set global output filename
    global OUTPUT_FILE
    add_type_suffix = not args.no_type_suffix
    if args.output_file:
        # User provided name: use the stem, extension is added per-format later
        op = Path(args.output_file)
        OUTPUT_FILE = op.stem
    elif OUTPUT_FILE is None:
        # Fall back to project name
        project_name = get_project_name_from_pyproject()
        OUTPUT_FILE = project_name
    # else: keep pre-set global OUTPUT_FILE as-is

    if add_type_suffix:
        OUTPUT_FILE = f"{OUTPUT_FILE}_{book_type.value}"

    print(f"📘 Output file base name set to: {OUTPUT_FILE}")

    # Determine language: CLI > metadata.yaml > fallback
    metadata_lang = get_metadata_language()
    cli_lang = args.lang

    if cli_lang:
        if metadata_lang and cli_lang != metadata_lang:
            print("\n⚠️⚠️⚠️ LANGUAGE MISMATCH DETECTED ⚠️⚠️⚠️")
            print(
                f"Metadata file says: '{metadata_lang}' but CLI argument is: '{cli_lang}'"
            )
            print("Using CLI argument value.\n")
        lang = cli_lang
    elif metadata_lang:
        lang = metadata_lang
        print(f"🌐 Using language from metadata.yaml: '{lang}'")
    else:
        print(f"cli_lang: '{cli_lang}'")
        lang = "en"
        print("⚠️ No language set in CLI or metadata.yaml. Defaulting to 'en'")

    # Step 1a: Normalize TOC (recommended: pure anchors, robust for single-file Markdown)
    try:
        if TOC_FILE.exists():
            # Choice: "strip-to-anchors" is safest.
            # If you want to keep paths, use mode=replace-ext instead and specify the extension.
            toc_mode = "strip-to-anchors"
            toc_ext = args.extension if args.extension else "md"
            subprocess.run(
                [
                    "python3",
                    NORMALIZE_TOC,
                    "--toc",
                    str(TOC_FILE),
                    "--mode",
                    toc_mode,
                    "--ext",
                    toc_ext,
                ],
                check=True,
                stdout=open(LOG_FILE, "a"),
                stderr=open(LOG_FILE, "a"),
            )
            print(f"✅ TOC normalized using mode={toc_mode}")
        else:
            print(f"ℹ️  No TOC file at {TOC_FILE}; skipping TOC normalization.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error normalizing TOC: {e}")

    # Step 1: Convert image paths to absolute
    # Run pre-processing scripts unless user opts out or wants to keep relative paths
    if not args.skip_images and not args.keep_relative_paths:
        run_script(ABSOLUTE_SCRIPT)  # Convert relative paths to absolute
        run_script(IMG_SCRIPT, "--to-absolute")  # Process image tags
    elif args.skip_images:
        print("⏭️  Skipping Step 1 (skip-images).")
    else:
        print("⏭️  Skipping Step 1 (keep relative paths).")

    # Step 2: Prepare environment
    prepare_output_folder()  # Prepare folders and backup if needed
    global METADATA_FILE
    METADATA_FILE, _is_temp_metadata = get_or_create_metadata_file(
        METADATA_FILE
    )  # Make sure metadata exists

    # Step 3: Compile book in requested formats
    # Determine formats to export
    # Step 3: Compile the book in requested formats
    selected_formats = args.format.split(",") if args.format else FORMATS.keys()

    for fmt in selected_formats:
        if fmt not in FORMATS:
            print(f"⚠️ Skipping unknown format: {fmt}")
            continue

        effective_order = (
            section_order
            if section_order is not None
            else pick_section_order(book_type, fmt)
        )

        # Warnen, falls die Print-ToC-Datei fehlt
        if "front-matter/toc_print_edition.md" in effective_order:
            toc_print_path = Path(BOOK_DIR) / "front-matter" / "toc_print_edition.md"
            if not toc_print_path.exists():
                print(
                    "⚠️ Print ToC file missing: manuscript/front-matter/toc_print_edition.md "
                    "(fallback to ebook toc.md)"
                )
                # Fallback: ersetze durch toc.md, falls vorhanden
                idx = effective_order.index("front-matter/toc_print_edition.md")
                effective_order = effective_order.copy()
                effective_order[idx] = "front-matter/toc.md"

        # TOC normalisieren NUR wenn es toc.md ist (ebook)
        toc_candidate = (
            Path(BOOK_DIR)
            / "front-matter"
            / (
                "toc.md"
                if "front-matter/toc.md" in effective_order
                else "toc_print_edition.md"
            )
        )
        normalize_toc_if_needed(toc_candidate, args)

        compile_book(fmt, effective_order, args.cover, args.epub2, lang, args.extension)

    # Step 4: Restore original image paths
    # Revert any image/URL changes made before compilation unless we kept relative paths
    if not args.skip_images and not args.keep_relative_paths:
        run_script(RELATIVE_SCRIPT)  # Convert absolute paths back to relative
        run_script(IMG_SCRIPT, "--to-relative")  # Revert image tag changes
    elif args.skip_images:
        print("⏭️  Skipping Step 4 (skip-images).")
    else:
        print("⏭️  Skipping Step 4 (keep relative paths).")

    # Step 5: Start background validation for each generated format
    threads = []

    for fmt in selected_formats:
        ext_for_fmt = resolve_ext(fmt, args.extension if fmt == "markdown" else None)
        output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{ext_for_fmt}")

        if fmt == "epub":
            thread = threading.Thread(
                target=validate_epub_with_epubcheck,
                args=(output_path,),
                name=f"Validate-{fmt.upper()}",
                daemon=False,
            )
            print("🧩 EPUB generated. Validation running in background...")
        elif fmt == "pdf":
            thread = threading.Thread(
                target=validate_pdf,
                args=(output_path,),
                name=f"Validate-{fmt.upper()}",
                daemon=False,
            )
            print("🧩 PDF generated. Validation running in background...")
        elif fmt == "docx":
            thread = threading.Thread(
                target=validate_docx,
                args=(output_path,),
                name=f"Validate-{fmt.upper()}",
                daemon=False,
            )
            print("🧩 DOCX generated. Validation running in background...")
        elif fmt == "markdown":
            thread = threading.Thread(
                target=validate_markdown,
                args=(output_path,),
                name=f"Validate-{fmt.upper()}",
                daemon=False,
            )
            print("🧩 Markdown generated. Validation running in background...")
        else:
            continue  # Skip unknown formats

        thread.start()
        threads.append(thread)

    # Optional: wait a moment for fast checks to finish (e.g. markdown)
    # But don't block long — let slow ones (epubcheck) continue
    print("\n🚀 Export completed. Background validation in progress...")
    print("📁 Outputs: ./output/")
    print("📄 Logs: ./export.log")
    print("🔍 Validation results will appear shortly.")
    if _is_temp_metadata:
        try:
            METADATA_FILE.unlink(missing_ok=True)
            print(f"🗑️ Deleted temporary metadata file: {METADATA_FILE}")
        except OSError as e:
            print(f"⚠️ Could not delete temporary metadata file {METADATA_FILE}: {e}")


# Entry point
if __name__ == "__main__":
    main()
