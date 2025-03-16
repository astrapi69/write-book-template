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
    if os.path.exists("output"):
        if os.path.exists("output_backup"):
            shutil.rmtree("output_backup")
        shutil.move("output", "output_backup")
    os.makedirs("output", exist_ok=True)

def compile_book(format):
    output_file = f"{OUTPUT_FILE}.{FORMATS[format]}"
    output_path = os.path.join(OUTPUT_DIR, output_file)

    page_break = PAGE_BREAKS.get(format, "\n\n")
    temp_markdown = os.path.join(OUTPUT_DIR, "combined_temp.md")

    # Sort chapter files
    chapters_dir = os.path.join(BOOK_DIR, "chapters")
    chapters = sorted(
        [f for f in os.listdir(chapters_dir) if f.endswith(".md")]
    )

    # Compile content into one markdown file
    with open(temp_markdown, "w", encoding="utf-8") as combined:
        for section in [
            "front-matter/book-title.md",
            "front-matter/toc.md",
            "front-matter/introduction.md",
            "front-matter/foreword.md",
            "front-matter/preface.md",
        ]:
            section_path = os.path.join(BOOK_DIR, section)
            if os.path.exists(section_path):
                with open(section_path, encoding="utf-8") as f:
                    combined.write(f.read() + page_break)

        for chapter in chapters_sorted():
            with open(chapter, encoding="utf-8") as ch:
                combined.write(ch.read() + page_break)

        for back_matter in [
            "back-matter/epilogue.md",
            "back-matter/glossary.md",
            "back-matter/about-the-author.md",
            "back-matter/acknowledgments.md",
            "back-matter/appendix.md",
            "back-matter/bibliography.md",
            "back-matter/faq.md",
            "back-matter/index.md",
        ]:
            back_matter_path = os.path.join(BOOK_DIR, back_matter)
            if os.path.exists(back_matter):
                with open(back_matter, "r", encoding="utf-8") as bm:
                    combined.write(bm.read() + page_break)

    pandoc_cmd = [
        "pandoc",
        "--from=markdown",
        f"--to={FORMATS[format]}",
        f"--output={output_path}",
        temp_markdown,
    ]

    try:
        subprocess.run(pandoc_cmd, check=True)
        print(f"✅ Successfully generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compiling {format}: {e}")

    # Clean temporary file
    os.remove(temp_markdown)

def chapters_sorted():
    chapters_dir = os.path.join(BOOK_DIR, "chapters")
    return [
        os.path.join(chapters_dir, f)
        for f in sorted(os.listdir(chapters_dir))
        if f.endswith(".md")
    ]

if __name__ == "__main__":
    # Variables
    BOOK_DIR = "./manuscript"
    OUTPUT_DIR = "./output"
    BACKUP_DIR = "./output_backup"
    OUTPUT_FILE = "book"  # Change as needed

    FORMATS = {
        "markdown": "gfm",
        "pdf": "pdf",
        "epub": "epub",
        "docx": "docx",
    }

    prepare_output_folder()

    for fmt in FORMATS.keys():
        compile_book(fmt)

    print("✅ All formats generated successfully!")
