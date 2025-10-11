# scripts/init_book_project.py
import json
from pathlib import Path
import toml

# Keep working directory handling simple for CLI; tests can pass base_dir explicitly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def update_pyproject(project_name: str, description: str, base_dir: Path):
    """Update project name and description in pyproject.toml"""
    pyproject_path = base_dir / "pyproject.toml"
    data = toml.load(pyproject_path)
    data["tool"]["poetry"]["name"] = project_name
    data["tool"]["poetry"]["description"] = description
    pyproject_path.write_text(toml.dumps(data), encoding="utf-8")
    print(f"✅ Updated pyproject.toml with name='{project_name}' and description.")


def update_full_export_script(
    output_file: str, title: str, author: str, year: str, lang: str, base_dir: Path
):
    """Update constants in scripts/full_export_book.py (string replace based on your placeholders)."""
    path = base_dir / "scripts/full_export_book.py"
    content = path.read_text(encoding="utf-8")

    content = content.replace(
        'OUTPUT_FILE = "book"                            # Base name for the output files #TODO replace with your data',
        f'OUTPUT_FILE = "{output_file}"                            # Base name for the output files',
    ).replace(
        "f.write(\"title: 'CHANGE TO YOUR TITLE'\\nauthor: 'YOUR NAME'\\ndate: '2025'\\nlang: 'en'\\n\") #TODO replace with your data",
        f"f.write(\"title: '{title}'\\nauthor: '{author}'\\ndate: '{year}'\\nlang: '{lang}'\\n\")",
    )

    path.write_text(content, encoding="utf-8")
    print("✅ Updated full_export_book.py with your metadata.")


def create_directories(base_path: Path, directories: list[str]):
    for dir_path in directories:
        (base_path / dir_path).mkdir(parents=True, exist_ok=True)


def create_files(base_path: Path, files: list[str]):
    for file_path in files:
        p = base_path / file_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()


def write_readme(readme_path: Path):
    readme_path.write_text(
        "# Book Project\nThis is the book project structure.\n", encoding="utf-8"
    )


def write_metadata_json(json_path: Path):
    """Template values users can later fill; ISBN is a mapping."""
    json_content = {
        "BOOK_TITLE": "",
        "BOOK_SUBTITLE": "",
        "AUTHOR_NAME": "",
        "ISBN": {"ebook": "", "paperback": "", "hardcover": ""},  # <-- nested
        "BOOK_EDITION": "",
        "PUBLISHER_NAME": "",
        "PUBLICATION_DATE": "",
        "LANGUAGE": "",
        "BOOK_DESCRIPTION": "",
        "KEYWORDS": [],
        "COVER_IMAGE": "",
        "OUTPUT_FORMATS": ["pdf", "epub", "mobi", "docx"],
        "KDP_ENABLED": False,
    }
    json_path.write_text(
        json.dumps(json_content, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def write_image_prompt_generation_template(json_path: Path):
    json_content = {
        "project_name": "your_project_name",
        "description": "Your description",
        "author": "Asterios Raptis",
        "language": "en",
        "structure": {
            "source_format": "Markdown",
            "chapter_path": "manuscript/chapters/",
            "assets_path": "assets/figures/",
            "cover_file": "assets/covers/cover.png",
            "image_prompt_file": "scripts/data/image_prompts.json",
        },
        "output_formats": ["epub", "epub2", "pdf", "docx", "md"],
        "image_generation": {
            "engine": "Stable Diffusion / DALL·E / Midjourney",
            "prompt_file": "scripts/data/image_prompts.json",
            "target_path": "assets/figures/",
            "style": "cinematic, sci-fi realism, moody lighting",
        },
        "tasks": [
            {
                "name": "Validate image prompts",
                "description": "Check each chapter has a matching prompt.",
            },
            {
                "name": "Insert illustrations",
                "description": "Add images to Markdown below the title.",
            },
            {
                "name": "Export final book",
                "description": "Run `poetry run full-export`.",
            },
            {
                "name": "Translate",
                "description": "Use DeepL / LM Studio scripts for translations.",
            },
        ],
        "notes": "Cover is generated. Keep prompt-file mapping stable.",
    }
    json_path.write_text(
        json.dumps(json_content, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_metadata_yaml_content(
    book_title: str, author_name: str, project_description: str, year: str, lang: str
) -> str:
    """Returns YAML text with nested ISBN mapping."""
    return f"""\
title: "{book_title}"
subtitle: ""
author: "{author_name}"
isbn:
  ebook: ""
  paperback: ""
  hardcover: ""
edition: "1"
publisher: ""
date: "{year}"
language: "{lang}"
description: "{project_description}"
keywords: []
cover_image: "assets/covers/cover.png"
output_formats: ["pdf", "epub", "docx"]
kdp_enabled: false
"""


def run_init_book_project(
    project_name: str,
    project_description: str,
    book_title: str,
    author_name: str,
    year: str = "2025",
    lang: str = "en",
    base_dir: Path | None = None,
):
    """Idempotent, testable entrypoint."""
    base = base_dir or PROJECT_ROOT

    # Create folders and files
    directories = [
        "manuscript/chapters",
        "manuscript/front-matter",
        "manuscript/back-matter",
        "assets/covers",
        "assets/author",
        "assets/figures/diagrams",
        "assets/figures/infographics",
        "config",
        "output",
        "scripts/data",
    ]
    files = [
        "manuscript/chapters/01-chapter.md",
        "manuscript/chapters/02-chapter.md",
        "manuscript/front-matter/imprint.md",
        "manuscript/front-matter/foreword.md",
        "manuscript/front-matter/preface.md",
        "manuscript/front-matter/toc.md",
        "manuscript/front-matter/toc_print_edition.md",
        "manuscript/back-matter/about-the-author.md",
        "manuscript/back-matter/acknowledgments.md",
        "manuscript/back-matter/appendix.md",
        "manuscript/back-matter/bibliography.md",
        "manuscript/back-matter/epilogue.md",
        "manuscript/back-matter/glossary.md",
        "config/amazon-kdp-info.md",
        "config/book-description.html",
        "config/cover-back-page-author-introduction.md",
        "config/cover-back-page-author-introduction.txt",
        "config/cover-back-page-description.md",
        "config/cover-back-page-description.txt",
        "config/keywords.md",
        "config/styles.css",
        "README.md",
        "LICENSE",
    ]
    create_directories(base, directories)
    create_files(base, files)
    write_readme(base / "README.md")
    write_metadata_json(base / "config/metadata_values.json")
    write_image_prompt_generation_template(
        base / "scripts/data/image_prompt_generation_template.json"
    )

    # Write metadata.yaml with nested ISBN
    metadata_path = base / "config/metadata.yaml"
    metadata_path.write_text(
        build_metadata_yaml_content(
            book_title, author_name, project_description, year, lang
        ),
        encoding="utf-8",
    )

    # Update pyproject.toml and scripts/full_export_book.py
    update_pyproject(project_name, project_description, base)
    update_full_export_script(
        output_file=project_name,
        title=book_title,
        author=author_name,
        year=year,
        lang=lang,
        base_dir=base,
    )

    print("✅ Book project structure created successfully!")
    print("🛠️  pyproject.toml and full_export_book.py updated.")
    print(
        "📁 Image generation template saved at scripts/data/image_prompt_generation_template.json"
    )
    print("📄 Metadata saved to config/metadata.yaml")


def main():
    # CLI flow
    project_name = input(
        "📘 Enter your project name (e.g., 'ai-for-everyone'): "
    ).strip()
    project_description = input(
        "📝 Enter a short description of your project: "
    ).strip()
    book_title = input("📖 Enter your book title: ").strip()
    author_name = input("👤 Enter the author's name: ").strip()
    year = "2025"
    lang = "en"

    run_init_book_project(
        project_name=project_name,
        project_description=project_description,
        book_title=book_title,
        author_name=author_name,
        year=year,
        lang=lang,
        base_dir=PROJECT_ROOT,
    )


if __name__ == "__main__":
    main()
