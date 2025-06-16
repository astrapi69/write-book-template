import os
from pathlib import Path
import shutil

import sys

# Add the directory of the script to sys.path
sys.path.append(str(Path(__file__).parent))

from emoji_map import EMOJI_MAP

# Optional: set to True to overwrite original files
OVERWRITE = True

# Change working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

BOOK_DIR = Path("./manuscript")
SECTIONS = ["front-matter", "chapters", "back-matter"]
SUFFIX = "-final.md"


def process_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    for emoji, symbol in EMOJI_MAP.items():
        content = content.replace(emoji, symbol)

    if OVERWRITE:
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Replaced in: {file_path.name}")
    else:
        final_path = file_path.parent / f"{file_path.stem}{SUFFIX}"
        with final_path.open("w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Converted: {file_path.name} → {final_path.name}")


def main():
    for section in SECTIONS:
        section_path = BOOK_DIR / section
        if not section_path.exists():
            continue

        for file in section_path.glob("*.md"):
            if file.name.endswith(".md.bak"):
                continue
            process_file(file)


if __name__ == "__main__":
    main()
