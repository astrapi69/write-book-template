import os
import argparse
from pathlib import Path

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")


def create_chapter_files(project_dir: str, total: int, start: int = None):
    # Default to current dir + manuscript/chapters if project_dir is empty
    if not project_dir.strip():
        chapter_dir = Path.cwd() / "manuscript" / "chapters"
    else:
        chapter_dir = Path(project_dir) / "manuscript" / "chapters"

    chapter_dir.mkdir(parents=True, exist_ok=True)

    # Determine starting point
    if start is None:
        existing = []
        for file in chapter_dir.glob("[0-9][0-9]-chapter.md"):
            try:
                num = int(file.name.split("-")[0])
                existing.append(num)
            except ValueError:
                continue
        start_num = max(existing) + 1 if existing else 1
    else:
        start_num = start

    end_num = start_num + total - 1

    for i in range(start_num, end_num + 1):
        filename = f"{i:02d}-chapter.md"
        filepath = chapter_dir / filename
        filepath.touch(exist_ok=True)
        print(f"✓ Created: {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Generate chapter Markdown files.")
    parser.add_argument(
        "--project-dir",
        type=str,
        default="",
        help="Root directory of the project (default: ./manuscript/chapters)"
    )
    parser.add_argument(
        "--total",
        type=int,
        required=True,
        help="Number of chapters to create"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Optional starting chapter number (e.g. 8)"
    )

    args = parser.parse_args()
    create_chapter_files(args.project_dir, args.total, args.start)

if __name__ == "__main__":
    main()
