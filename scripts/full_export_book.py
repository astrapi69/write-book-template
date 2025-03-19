import os
import shutil
import subprocess
import argparse

# Change working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define directories
BOOK_DIR = "./manuscript"
OUTPUT_DIR = "./output"
BACKUP_DIR = "./output_backup"
OUTPUT_FILE = "ai_for_everyone_book"
METADATA_FILE = "config/metadata.yaml"

SCRIPT_DIR = "./scripts"
ABSOLUTE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_absolute.py")
RELATIVE_SCRIPT = os.path.join(SCRIPT_DIR, "convert_to_relative.py")
IMG_SCRIPT = os.path.join(SCRIPT_DIR, "convert_img_tags.py")

FORMATS = {
    "markdown": "gfm",
    "pdf": "pdf",
    "epub": "epub",
    "docx": "docx",
}

LOG_FILE = "export.log"

def run_script(script_path, arg=None):
    """ Run a Python script safely. """
    try:
        if arg:
            subprocess.run(["python3", script_path, arg], check=True, stdout=open("export.log", "a"), stderr=open("export.log", "a"))
        else:
            subprocess.run(["python3", script_path], check=True, stdout=open("export.log", "a"), stderr=open("export.log", "a"))
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
    """ Ensure metadata.yaml exists to avoid Pandoc warnings. """
    if not os.path.exists(METADATA_FILE):
        print(f"⚠️ Metadata file missing! Creating default {METADATA_FILE}.")
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            f.write("title: 'AI for Everyone'\nauthor: 'Your Name'\ndate: '2025'\n")

def compile_book(format):
    """ Compile the book into the specified format using Pandoc. """
    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{FORMATS[format]}")

    md_files = []
    for section in ["front-matter", "chapters", "back-matter"]:
        section_path = os.path.join(BOOK_DIR, section)
        if os.path.exists(section_path):
            md_files.extend(
                sorted(os.path.join(section_path, f) for f in os.listdir(section_path) if f.endswith(".md"))
            )

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
        pandoc_cmd.append("--pdf-engine=pdflatex")

    try:
        with open(LOG_FILE, "a") as log_file:
            subprocess.run(pandoc_cmd, check=True, stdout=log_file, stderr=log_file)

        print(f"✅ Successfully generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compiling {format}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Export AI for Everyone book.")
    parser.add_argument("--skip-images", action="store_true", help="Skip image conversion scripts.")
    parser.add_argument("--format", type=str, help="Specify formats (comma-separated, e.g., pdf,epub).")

    args = parser.parse_args()

    # Step 1: Convert relative paths to absolute (Markdown images and HTML <img>)
    if not args.skip_images:
        run_script(ABSOLUTE_SCRIPT)
        run_script(IMG_SCRIPT, "--to-absolute")

    # Step 2: Prepare output folder
    prepare_output_folder()

    # Step 3: Ensure metadata file exists
    ensure_metadata_file()

    # Step 4: Export book in selected formats (default: all)
    selected_formats = args.format.split(",") if args.format else FORMATS.keys()

    for fmt in selected_formats:
        if fmt in FORMATS:
            compile_book(fmt)
        else:
            print(f"⚠️ Skipping unknown format: {fmt}")

    # Step 5: Convert absolute paths back to relative (Markdown images and HTML <img>)
    if not args.skip_images:
        run_script(RELATIVE_SCRIPT)
        run_script(IMG_SCRIPT, "--to-relative")

    print("🎉 All formats generated successfully! Check export.log for details.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export AI for Everyone book.")
    parser.add_argument("--skip-images", action="store_true", help="Skip image conversion scripts.")
    parser.add_argument("--format", type=str, help="Specify formats (comma-separated, e.g., pdf,epub).")

    args = parser.parse_args()

    # Step 1: Convert relative paths to absolute (Markdown images and HTML <img>)
    if not args.skip_images:
        run_script(ABSOLUTE_SCRIPT)
        run_script(IMG_SCRIPT, "--to-absolute")

    # Step 2: Prepare output folder
    prepare_output_folder()

    # Step 3: Ensure metadata file exists
    ensure_metadata_file()

    # Step 4: Export book in selected formats (default: all)
    selected_formats = args.format.split(",") if args.format else FORMATS.keys()

    for fmt in selected_formats:
        if fmt in FORMATS:
            compile_book(fmt)
        else:
            print(f"⚠️ Skipping unknown format: {fmt}")

    # Step 5: Convert absolute paths back to relative (Markdown images and HTML <img>)
    if not args.skip_images:
        run_script(RELATIVE_SCRIPT)
        run_script(IMG_SCRIPT, "--to-relative")

    print("🎉 All formats generated successfully! Check export.log for details.")
