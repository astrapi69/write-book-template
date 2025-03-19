import os
import re
from pathlib import Path

# Automatically detect the project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # Go one level up to project root
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Directories to scan
MD_DIRECTORIES = [
    MANUSCRIPT_DIR / "chapters",
    MANUSCRIPT_DIR / "front-matter",
    MANUSCRIPT_DIR / "back-matter",
]

# Regex pattern for HTML <img> tags
html_img_pattern = re.compile(r'<img src="(.*?)" alt="(.*?)"(.*?)>')


def convert_to_absolute():
    """ Convert relative <img> src paths to absolute paths. """
    for md_dir in MD_DIRECTORIES:
        if not md_dir.exists():
            continue

        for md_file in md_dir.rglob("*.md"):
            with open(md_file, "r", encoding="utf-8") as file:
                content = file.read()

            updated_content = content

            # Convert <img> src to absolute path
            for match in html_img_pattern.findall(content):
                image_path, alt_text, rest = match
                if not os.path.isabs(image_path):
                    abs_path = (md_file.parent / image_path).resolve()
                    if abs_path.exists():
                        new_tag = f'<img src="{abs_path}" alt="{alt_text}"{rest}>'
                        updated_content = updated_content.replace(f'<img src="{image_path}" alt="{alt_text}"{rest}>',
                                                                  new_tag)
                        print(f"✅ Converted HTML <img>: {image_path} -> {abs_path}")

            # Save the updated file
            with open(md_file, "w", encoding="utf-8") as file:
                file.write(updated_content)

    print("✅ All Markdown files updated with absolute paths for <img> tags.")


def convert_to_relative():
    """ Convert absolute <img> src paths back to relative paths. """
    for md_dir in MD_DIRECTORIES:
        if not md_dir.exists():
            continue

        for md_file in md_dir.rglob("*.md"):
            with open(md_file, "r", encoding="utf-8") as file:
                content = file.read()

            updated_content = content

            # Convert <img> src to relative path
            for match in html_img_pattern.findall(content):
                abs_path, alt_text, rest = match
                abs_path = Path(abs_path)

                if abs_path.is_absolute() and ASSETS_DIR in abs_path.parents:
                    relative_path = os.path.relpath(abs_path, start=md_file.parent)
                    new_tag = f'<img src="{relative_path}" alt="{alt_text}"{rest}>'
                    updated_content = updated_content.replace(f'<img src="{abs_path}" alt="{alt_text}"{rest}>', new_tag)
                    print(f"🔄 Reverted: {abs_path} -> {relative_path}")

            # Save the updated file
            with open(md_file, "w", encoding="utf-8") as file:
                file.write(updated_content)

    print("🔄 All Markdown files reverted to relative paths for <img> tags.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert <img> src paths between relative and absolute.")
    parser.add_argument("--to-absolute", action="store_true", help="Convert relative paths to absolute paths.")
    parser.add_argument("--to-relative", action="store_true", help="Convert absolute paths to relative paths.")

    args = parser.parse_args()

    if args.to_absolute:
        convert_to_absolute()
    elif args.to_relative:
        convert_to_relative()
    else:
        print("❌ Please specify --to-absolute or --to-relative.")
