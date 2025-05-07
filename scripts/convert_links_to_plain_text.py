import re
from pathlib import Path
import os

# Change working directory to project root (parent directory of scripts/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Target file paths for print conversion
FILE_PATHS = [
    Path("./manuscript/back-matter/about-the-author.md"),
]


def convert_links_to_print_style(filepath: Path):
    content = filepath.read_text(encoding="utf-8")

    # Convert [Label](URL) to Label: URL
    converted = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1: \2', content)

    filepath.write_text(converted, encoding="utf-8")
    print(f"✓ Converted links to print-safe format in: {filepath}")


if __name__ == "__main__":
    for file_path in FILE_PATHS:
        if file_path.exists():
            convert_links_to_print_style(file_path)
        else:
            print(f"❌ File not found: {file_path}")
