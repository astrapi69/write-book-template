#!/usr/bin/env python3

import os
import argparse
import re
from pathlib import Path

DEFAULT_CHAPTER_DIR = "./manuscript/chapters"
DEFAULT_OUTPUT_FILE = "./output/book-combined.html"
DEFAULT_STYLESHEET_PATH = "./config/comic.css"
DEFAULT_TITLE = "Untitled Book"
DEFAULT_LANG = "en"

def combine_html_chapters(chapter_dir, output_file, title, lang, stylesheet_path):
    def chapter_sort_key(path):
        match = re.match(r"(\d+)", path.stem)
        return int(match.group(1)) if match else 0

    chapter_files = sorted(Path(chapter_dir).glob("*.html"), key=chapter_sort_key)
    if not chapter_files:
        print(f"❌ No .html files found in {chapter_dir}")
        return

    os.makedirs(Path(output_file).parent, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n')
        outfile.write('  <meta charset="UTF-8">\n')
        outfile.write(f'  <title>{title}</title>\n')
        outfile.write(f'  <link rel="stylesheet" href="{stylesheet_path}">\n')
        outfile.write('</head>\n<body>\n')

        for chapter_file in chapter_files:
            with open(chapter_file, "r", encoding="utf-8") as infile:
                inside_body = False
                for line in infile:
                    if "<body" in line:
                        inside_body = True
                        continue
                    if inside_body:
                        if "</body>" in line:
                            break
                        outfile.write(line)

        outfile.write('</body>\n</html>\n')

    print(f"✅ Combined HTML saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Combine HTML chapters into one HTML document.")
    parser.add_argument("--chapter-dir", default=DEFAULT_CHAPTER_DIR, help="Directory containing HTML chapters")
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE, help="Output HTML file")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="HTML title of the combined document")
    parser.add_argument("--lang", default=DEFAULT_LANG, help="Language tag (e.g. 'en', 'de')")
    parser.add_argument("--stylesheet", default=DEFAULT_STYLESHEET_PATH, help="Path to CSS stylesheet")

    args = parser.parse_args()

    combine_html_chapters(
        chapter_dir=args.chapter_dir,
        output_file=args.output_file,
        title=args.title,
        lang=args.lang,
        stylesheet_path=args.stylesheet
    )

if __name__ == "__main__":
    main()
