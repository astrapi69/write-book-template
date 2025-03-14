import os
import shutil
import subprocess

BOOK_DIR = "./manuscript"
OUTPUT_DIR = "./output"
OUTPUT_FILE = "book" # change to specific book name
BACKUP_DIR = "./output_backup"

FORMATS = {
    "markdown": "gfm",  # Changed "md" to "gfm" (GitHub Flavored Markdown) to be valid for Pandoc
    "pdf": "pdf",
    "epub": "epub",
    "docx": "docx",
}

PAGE_BREAKS = {
    "pdf": "\\newpage\n\n",
    "docx": "---\n\n",  # Horizontal rule for section break in DOCX
    "epub": "<br style='page-break-before:always'/>\n\n",  # Page break for EPUB
}

def prepare_output_folder():
    if os.path.exists(OUTPUT_DIR):
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)  # Remove old backup
        shutil.move(OUTPUT_DIR, BACKUP_DIR)  # Move current output to backup
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def compile_book(format):
    if format not in FORMATS:
        raise ValueError(f"Unsupported format: {format}")

    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{FORMATS[format]}")
    page_break = PAGE_BREAKS.get(format, "\n\n")
    chapter_files = sorted(
        [os.path.join(BOOK_DIR, "chapters", f) for f in os.listdir(os.path.join(BOOK_DIR, "chapters")) if f.endswith(".md")]
    )

    # Create a temp file for proper page breaks (explicit UTF-8 encoding)
    temp_markdown_file = os.path.join(OUTPUT_DIR, "temp_book.md")
    with open(temp_markdown_file, "w", encoding="utf-8") as temp_file:  # ✅ Fix: UTF-8 Encoding
        for section in [
            "front-matter/book-title.md",
            "front-matter/toc.md",
            "front-matter/introduction.md",
            "front-matter/foreword.md",
            "front-matter/preface.md",
        ]:
            section_path = os.path.join(BOOK_DIR, section)
            if os.path.exists(section_path):
                with open(section_path, encoding="utf-8") as f:  # ✅ Fix: Ensure UTF-8 while reading
                    temp_file.write(f.read() + page_break)

        for chapter in chapter_files:
            with open(chapter, encoding="utf-8") as f:  # ✅ Fix: Ensure UTF-8 while reading
                temp_file.write(f.read() + "\n\n")

        for back_matter in [
            "back-matter/epilogue.md",
            "back-matter/glossary.md",
            "back-matter/about-the-author.md",
            "back-matter/acknowledgments.md",
        ]:
            back_matter_path = os.path.join(BOOK_DIR, back_matter)
            if os.path.exists(back_matter_path):
                with open(back_matter_path, encoding="utf-8") as f:  # ✅ Fix: Ensure UTF-8 while reading
                    temp_file.write(f.read() + "\n\n")

    command = [
        "pandoc",
        "--from=markdown",
        "--to=" + FORMATS[format],
        "--output=" + output_path,
        temp_markdown_file,
        ]

    # Add PDF engine for better page breaks in PDF
    if format == "pdf":
        command.append("--pdf-engine=pdflatex")

    try:
        subprocess.run(command, check=True)
        print(f"Book compiled to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling book: {e}")

if __name__ == "__main__":
    prepare_output_folder()
    for fmt in FORMATS.keys():
        compile_book(fmt)
