# scripts/full_export_comic.py
import re
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple

NUM_PREFIX = re.compile(r"^(\d+)")  # e.g. "01-intro.html" -> 1


def _chapter_sort_key(path: Path) -> Tuple[int, str]:
    """
    Sort by leading integer (if present), then by full filename for stability.
    """
    m = NUM_PREFIX.match(path.stem)
    return (int(m.group(1)) if m else 10**9, path.name)


def _extract_body(html_text: str) -> str:
    """
    Return the contents inside <body>...</body>.
    If no <body> exists, return the whole document.
    A minimal, fast and robust method that tolerates attributes/whitespace.
    """
    # cheap, case-insensitive search
    lower = html_text.lower()
    start = lower.find("<body")
    if start == -1:
        return html_text
    start = lower.find(">", start)
    if start == -1:
        return html_text
    end = lower.find("</body>", start)
    if end == -1:
        end = len(html_text)
    return html_text[start + 1 : end]


def combine_html_chapters(
    chapter_dir: str,
    output_file: str,
    title: str = "Die Nasenbohrer-Chroniken",
    lang: str = "de",
    stylesheet_path: str = "config/comic.css",
) -> List[Path]:
    """
    Combine all .html files from `chapter_dir` (sorted by numeric prefix) into a single HTML file.

    Returns the list of chapter files that were included (in order).
    Raises FileNotFoundError if directory doesn’t exist or contains no .html files.
    """
    chapter_dir_path = Path(chapter_dir)
    if not chapter_dir_path.exists():
        raise FileNotFoundError(f"Chapter directory not found: {chapter_dir}")

    chapter_files = sorted(chapter_dir_path.glob("*.html"), key=_chapter_sort_key)
    if not chapter_files:
        raise FileNotFoundError(f"No .html files found in: {chapter_dir}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as outfile:
        outfile.write(f'<!DOCTYPE html>\n<html lang="{lang}">\n<head>\n')
        outfile.write('  <meta charset="UTF-8">\n')
        outfile.write(
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        )
        outfile.write(f"  <title>{title}</title>\n")
        outfile.write(f'  <link rel="stylesheet" href="{stylesheet_path}">\n')
        outfile.write("</head>\n<body>\n")

        for chapter_file in chapter_files:
            html_text = chapter_file.read_text(encoding="utf-8", errors="replace")
            body = _extract_body(html_text).strip()
            if body:
                # Add a marker for debugging/anchoring (does not affect layout)
                outfile.write(f"<!-- BEGIN {chapter_file.name} -->\n")
                outfile.write(body)
                outfile.write(f"\n<!-- END {chapter_file.name} -->\n\n")

        outfile.write("</body>\n</html>\n")

    print(f"✅ HTML kombiniert in: {output_path}")
    return chapter_files


def export_pdf_from_html(
    input_html: str,
    output_pdf: str,
    pdf_engine: str = "lualatex",
    mainfont: str = "DejaVu Sans",
    monofont: str = "DejaVu Sans Mono",
    extra_args: List[str] | None = None,
) -> bool:
    """
    Export a single HTML file to PDF via pandoc. Returns True on success, False otherwise.

    `extra_args` lets you pass through additional pandoc flags if needed.
    """
    cmd = [
        "pandoc",
        input_html,
        "-o",
        output_pdf,
        "--pdf-engine",
        pdf_engine,
        "-V",
        f"mainfont={mainfont}",
        "-V",
        f"monofont={monofont}",
    ]
    if extra_args:
        cmd.extend(extra_args)

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ PDF erfolgreich erstellt: {output_pdf}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Fehler beim PDF-Export: {e}")
        return False


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="📚 Comic HTML-Kapitel kombinieren und optional als PDF exportieren"
    )
    parser.add_argument(
        "--chapter-dir",
        type=str,
        default="./manuscript/chapters",
        help="Pfad zum Kapitelverzeichnis",
    )
    parser.add_argument(
        "--output-html",
        type=str,
        default="./output/nasenbohrer-komplett.html",
        help="Ziel-HTML-Datei",
    )
    parser.add_argument(
        "--output-pdf",
        type=str,
        default="./output/nasenbohrer-komplett.pdf",
        help="Ziel-PDF-Datei (wenn --pdf verwendet wird)",
    )
    parser.add_argument(
        "--stylesheet", type=str, default="config/comic.css", help="Pfad zur CSS-Datei"
    )
    parser.add_argument(
        "--title", type=str, default="Die Nasenbohrer-Chroniken", help="Titel der Seite"
    )
    parser.add_argument(
        "--lang", type=str, default="de", help="Sprache der Seite (lang-Attribut)"
    )
    parser.add_argument(
        "--pdf", action="store_true", help="Auch ein PDF mit Pandoc erzeugen"
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        combine_html_chapters(
            chapter_dir=args.chapter_dir,
            output_file=args.output_html,
            title=args.title,
            lang=args.lang,
            stylesheet_path=args.stylesheet,
        )
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    if args.pdf:
        ok = export_pdf_from_html(args.output_html, args.output_pdf)
        return 0 if ok else 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
