import os
import re
import subprocess
import argparse
from pathlib import Path

def combine_html_chapters(
    chapter_dir: str,
    output_file: str,
    title: str = "Die Nasenbohrer-Chroniken",
    lang: str = "de",
    stylesheet_path: str = "config/comic.css"
):
    def chapter_sort_key(path):
        match = re.match(r"(\d+)", path.stem)
        return int(match.group(1)) if match else 0

    chapter_files = sorted(Path(chapter_dir).glob("*.html"), key=chapter_sort_key)
    if not chapter_files:
        print(f"❌ Keine .html-Dateien in {chapter_dir} gefunden.")
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
    print(f"✅ HTML kombiniert in: {output_file}")

def export_pdf_from_html(input_html: str, output_pdf: str):
    try:
        subprocess.run(
            [
                "pandoc",
                input_html,
                "-o", output_pdf,
                "--pdf-engine=lualatex",
                "-V", "mainfont=DejaVu Sans",
                "-V", "monofont=DejaVu Sans Mono",
            ],
            check=True
        )
        print(f"✅ PDF erfolgreich erstellt: {output_pdf}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim PDF-Export: {e}")

def main():
    parser = argparse.ArgumentParser(description="📚 Comic HTML-Kapitel kombinieren und optional als PDF exportieren")
    parser.add_argument("--chapter-dir", type=str, default="./manuscript/chapters", help="Pfad zum Kapitelverzeichnis")
    parser.add_argument("--output-html", type=str, default="./output/nasenbohrer-komplett.html", help="Ziel-HTML-Datei")
    parser.add_argument("--output-pdf", type=str, default="./output/nasenbohrer-komplett.pdf", help="Ziel-PDF-Datei (wenn --pdf verwendet wird)")
    parser.add_argument("--stylesheet", type=str, default="config/comic.css", help="Pfad zur CSS-Datei")
    parser.add_argument("--title", type=str, default="Die Nasenbohrer-Chroniken", help="Titel der Seite")
    parser.add_argument("--lang", type=str, default="de", help="Sprache der Seite (lang-Attribut)")
    parser.add_argument("--pdf", action="store_true", help="Auch ein PDF mit Pandoc erzeugen")

    args = parser.parse_args()

    combine_html_chapters(
        chapter_dir=args.chapter_dir,
        output_file=args.output_html,
        title=args.title,
        lang=args.lang,
        stylesheet_path=args.stylesheet
    )

    if args.pdf:
        export_pdf_from_html(args.output_html, args.output_pdf)

if __name__ == "__main__":
    main()
