import os
import re
import argparse
from pathlib import Path

# Automatically detect the project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # Go one level up to project root
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"

# Default directories to scan
DEFAULT_DIRECTORIES = [
    MANUSCRIPT_DIR / "chapters",
    MANUSCRIPT_DIR / "front-matter",
    MANUSCRIPT_DIR / "back-matter",
]

# Regex pattern for Markdown image syntax
md_image_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")


def convert_to_absolute(directories):
    """ Convert relative Markdown image paths to absolute paths. """
    for md_dir in directories:
        md_dir = Path(md_dir).resolve()
        if not md_dir.exists():
            print(f"⚠️ Skipping non-existent directory: {md_dir}")
            continue

        for md_file in md_dir.rglob("*.md"):
            with open(md_file, "r", encoding="utf-8") as file:
                content = file.read()

            updated_content = content

            # Convert Markdown-style images
            for match in md_image_pattern.findall(content):
                alt_text, image_path = match
                if not os.path.isabs(image_path):  # Convert only relative paths
                    abs_path = (md_file.parent / image_path).resolve()
                    if abs_path.exists():
                        updated_content = updated_content.replace(f"![{alt_text}]({image_path})",
                                                                  f"![{alt_text}]({abs_path})")
                        print(f"✅ Converted Markdown image: {image_path} -> {abs_path}")

            # Save the updated file
            with open(md_file, "w", encoding="utf-8") as file:
                file.write(updated_content)

    print("✅ All Markdown files updated with absolute paths for images.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert relative image paths in Markdown files to absolute paths.")
    parser.add_argument(
        "directories",
        nargs="*",  # Accepts zero or more directories
        default=[str(d) for d in DEFAULT_DIRECTORIES],  # Default to predefined directories
        help="List of directories containing Markdown files (default: chapters, front-matter, back-matter)",
    )
    args = parser.parse_args()

    convert_to_absolute(args.directories)
