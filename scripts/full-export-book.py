import os
import shutil
import subprocess

# Change working directory to project root (parent directory of scripts/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Define project directories
BOOK_DIR = "./manuscript"
OUTPUT_DIR = "./output"
BACKUP_DIR = "./output_backup"
OUTPUT_FILE = "book"  # TODO change to your specific book name and delete this comment

FORMATS = {
    "markdown": "gfm",  # Changed "md" to "gfm" (GitHub Flavored Markdown) to be valid for Pandoc
    "pdf": "pdf",
    "epub": "epub",
    "docx": "docx",
}

PAGE_BREAKS = {
    "pdf": "\\newpage\n\n",
    "epub": "<div style='page-break-after:always'></div>\n\n",
    "docx": "\n\n", # Horizontal rule for section break in DOCX
    "markdown": "\n\n",
}

def prepare_output_folder():
    """Prepare output folder by backing up the existing output directory."""
    if os.path.exists(OUTPUT_DIR):
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)
        shutil.move(OUTPUT_DIR, BACKUP_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def compile_book(format):
    """Compile the book into the specified format using Pandoc."""
    output_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILE}.{FORMATS[format]}")
    page_break = PAGE_BREAKS.get(format, "\n\n")

    temp_markdown_file = os.path.join(OUTPUT_DIR, "temp_book.md")
    metadata_file = os.path.join("config", "metadata.yaml")  # Metadata file path

    # Gather chapters sorted
    chapter_files = sorted([
        os.path.join(BOOK_DIR, "chapters", f)
        for f in os.listdir(os.path.join(BOOK_DIR, "chapters"))
        if f.endswith(".md")
    ])

    with open(temp_markdown_file, "w", encoding="utf-8") as combined:
        # Front matter
        front_matter_files = [
            "front-matter/book-title.md",
            "front-matter/toc.md",
            "front-matter/introduction.md",
            "front-matter/foreword.md",
            "front-matter/preface.md",
        ]
        for file in front_matter_files:
            path = os.path.join(BOOK_DIR, file)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    combined.write(f.read() + page_break)

        # Chapters
        for chapter_file in chapter_files:
            with open(chapter_file, encoding="utf-8") as f:
                combined.write(f.read() + page_break)

        # Back matter
        back_matter_files = [
            "back-matter/epilogue.md",
            "back-matter/glossary.md",
            "back-matter/appendix.md",
            "back-matter/acknowledgments.md",
            "back-matter/about-the-author.md",
            "back-matter/faq.md",
            "back-matter/bibliography.md",
            "back-matter/index.md",
        ]
        for file in back_matter_files:
            path = os.path.join(BOOK_DIR, file)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    combined.write(f.read() + page_break)

    # Construct Pandoc command
    pandoc_cmd = [
        "pandoc",
        temp_markdown_file,
        "--from=markdown",
        f"--to={FORMATS[format]}",
        f"--output={output_path}",
        f"--metadata-file={metadata_file}",  # Include metadata file
    ]

    if format == "pdf":
        pandoc_cmd.append("--pdf-engine=pdflatex")

    try:
        subprocess.run(pandoc_cmd, check=True)
        print(f"✅ Successfully generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compiling {format}: {e}")

    # Uncomment the following line if you want to clean the temporary markdown file
    # os.remove(temp_markdown_file)

if __name__ == "__main__":
    prepare_output_folder()

    for fmt in FORMATS.keys():
        compile_book(fmt)

    print("🎉 All formats generated successfully!")
