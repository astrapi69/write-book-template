import re
from pathlib import Path
import os

# Change working directory to project root (parent directory of scripts/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define TOC file path
TOC_FILE_PATH = Path("./manuscript/front-matter/toc.md")


def strip_links(filepath: Path):
    content = filepath.read_text(encoding="utf-8")
    stripped = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
    filepath.write_text(stripped, encoding="utf-8")
    print(f"✓ Stripped links from: {filepath}")


if __name__ == "__main__":
    if TOC_FILE_PATH.exists():
        strip_links(TOC_FILE_PATH)
    else:
        print(f"❌ File not found: {TOC_FILE_PATH}")
