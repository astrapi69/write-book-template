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

# Regular expression to find image references with absolute paths
image_pattern = re.compile(r"!\[(.*?)\]\((/.*?\.(png|jpg|jpeg|svg|gif))\)")

# Convert absolute paths back to relative paths
for md_dir in MD_DIRECTORIES:
    if not md_dir.exists():
        continue  # Skip if the directory doesn't exist

    for md_file in md_dir.rglob("*.md"):
        with open(md_file, "r", encoding="utf-8") as file:
            content = file.read()

        updated_content = content
        for match in image_pattern.findall(content):
            alt_text, abs_path, ext = match

            # Convert absolute path to a relative path if it's within the assets directory
            abs_path = Path(abs_path)
            if abs_path.is_absolute() and ASSETS_DIR in abs_path.parents:
                relative_path = os.path.relpath(abs_path, start=md_file.parent)
                updated_content = updated_content.replace(str(abs_path), relative_path)
                print(f"🔄 Reverted: {abs_path} -> {relative_path}")

        # Save the modified Markdown file
        with open(md_file, "w", encoding="utf-8") as file:
            file.write(updated_content)

print("🔄 All Markdown files reverted to relative paths.")
