# init_book_project.py
import os
import json
from pathlib import Path
import toml

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")


def update_pyproject(project_name: str, description: str):
    """Update project name and description in pyproject.toml"""
    pyproject_path = "pyproject.toml"
    with open(pyproject_path, "r", encoding="utf-8") as f:
        data = toml.load(f)

    data["tool"]["poetry"]["name"] = project_name
    data["tool"]["poetry"]["description"] = description

    with open(pyproject_path, "w", encoding="utf-8") as f:
        toml.dump(data, f)
    print(f"✅ Updated pyproject.toml with name='{project_name}' and description.")

def update_full_export_script(output_file: str, title: str, author: str, year: str = "2025", lang: str = "en"):
    """Update constants in full_export_book.py"""
    path = "scripts/full_export_book.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        'OUTPUT_FILE = "book"                            # Base name for the output files #TODO replace with your data',
        f'OUTPUT_FILE = "{output_file}"                            # Base name for the output files'
    )
    content = content.replace(
        'f.write("title: \'CHANGE TO YOUR TITLE\'\\nauthor: \'YOUR NAME\'\\ndate: \'2025\'\\nlang: \'en\'\\n") #TODO replace with your data',
        f'f.write("title: \'{title}\'\\nauthor: \'{author}\'\\ndate: \'{year}\'\\nlang: \'{lang}\'\\n")'
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Updated full_export_book.py with your metadata.")


def create_directories(base_path: Path, directories: list[str]):
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

def create_files(base_path: Path, files: list[str]):
    for file_path in files:
        full_path = base_path / file_path
        full_path.touch()

def write_readme(readme_path: Path):
    readme_path.write_text("# Book Project\nThis is the book project structure.\n", encoding="utf-8")

def write_metadata_yaml(yaml_path: Path):
    yaml_content = """\
title: "{{BOOK_TITLE}}"
subtitle: "{{BOOK_SUBTITLE}}"
author: "{{AUTHOR_NAME}}"
isbn: "{{ISBN_NUMBER}}"
edition: "{{BOOK_EDITION}}"
publisher: "{{PUBLISHER_NAME}}"
date: "{{PUBLICATION_DATE}}"
language: "{{LANGUAGE}}"
description: "{{BOOK_DESCRIPTION}}"
keywords: {{KEYWORDS}}
cover_image: "{{COVER_IMAGE}}"
output_formats: {{OUTPUT_FORMATS}}
kdp_enabled: {{KDP_ENABLED}}
"""
    yaml_path.write_text(yaml_content, encoding="utf-8")

def write_metadata_json(json_path: Path):
    json_content = {
        "BOOK_TITLE": "",
        "BOOK_SUBTITLE": "",
        "AUTHOR_NAME": "",
        "ISBN_NUMBER": "",
        "BOOK_EDITION": "",
        "PUBLISHER_NAME": "",
        "PUBLICATION_DATE": "",
        "LANGUAGE": "",
        "BOOK_DESCRIPTION": "",
        "KEYWORDS": [],
        "COVER_IMAGE": "",
        "OUTPUT_FORMATS": ["pdf", "epub", "mobi", "docx"],
        "KDP_ENABLED": False
    }
    json_path.write_text(json.dumps(json_content, indent=2), encoding="utf-8")

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
            "image_prompt_file": "scripts/data/image_prompts.json"
        },
        "output_formats": ["epub", "epub2", "pdf", "docx", "md"],
        "image_generation": {
            "engine": "Stable Diffusion / DALL·E / Midjourney",
            "prompt_file": "scripts/data/image_prompts.json",
            "target_path": "assets/figures/",
            "style": "cinematic, sci-fi realism, moody lighting"
        },
        "tasks": [
            {
                "name": "Validate image prompts",
                "description": "Check if each chapter in the manuscript has a matching image prompt with filename and proper placement."
            },
            {
                "name": "Insert illustrations",
                "description": "Add images to Markdown files below the chapter title using the format: ![description](../../assets/filename.png)"
            },
            {
                "name": "Export final book",
                "description": "Use the CLI script `poetry run full-export` to create all final output formats."
            },
            {
                "name": "Translate",
                "description": "Use `translate-book-deepl.py` or `translate-book-lmstudio.py` to translate the book into English, Spanish or French."
            }
        ],
        "notes": "Das Cover ist generiert und befindet sich im angegebenen Pfad. Die Kapitel sind fortlaufend nummeriert, und alle Bilder sollen visuell stimmig zur jeweiligen Szene sein. Bitte bei Änderungen am Prompt-File die Zuordnung beibehalten."
    }
    json_path.write_text(json.dumps(json_content, indent=2, ensure_ascii=False), encoding="utf-8")

def main():
    base = Path(__file__).resolve().parent.parent

    # Prompt for user input
    project_name = input("📘 Enter your project name (e.g., 'ai-for-everyone'): ").strip()
    project_description = input("📝 Enter a short description of your project: ").strip()
    book_title = input("📖 Enter your book title: ").strip()
    author_name = input("👤 Enter the author's name: ").strip()
    year = "2025"
    lang = "en"

    # Update pyproject.toml and full_export_book.py
    update_pyproject(project_name, project_description)
    update_full_export_script(output_file=project_name, title=book_title, author=author_name, year=year, lang=lang)

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
        "scripts/data"
    ]

    files = [
        "manuscript/chapters/01-chapter.md",
        "manuscript/chapters/02-chapter.md",
        "manuscript/front-matter/book-title.md",
        "manuscript/front-matter/foreword.md",
        "manuscript/front-matter/preface.md",
        "manuscript/front-matter/toc.md",
        "manuscript/back-matter/about-the-author.md",
        "manuscript/back-matter/acknowledgments.md",
        "manuscript/back-matter/appendix.md",
        "manuscript/back-matter/bibliography.md",
        "manuscript/back-matter/epilogue.md",
        "manuscript/back-matter/faq.md",
        "manuscript/back-matter/glossary.md",
        "manuscript/back-matter/index.md",
        "config/amazon-kdp-info.md",
        "config/book-description.html",
        "config/cover-back-page-author-introduction.md",
        "config/cover-back-page-description.md",
        "config/keywords.md",
        "config/styles.css",
        "README.md",
        "LICENSE"
    ]

    create_directories(base, directories)
    create_files(base, files)
    write_readme(base / "README.md")
    write_metadata_json(base / "config/metadata_values.json")
    write_image_prompt_generation_template(base / "scripts/data/image_prompt_generation_template.json")

    # Generate metadata.yaml with actual input values
    metadata_path = base / "config/metadata.yaml"
    metadata_content = f"""\
title: "{book_title}"
subtitle: ""
author: "{author_name}"
isbn: ""
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
    metadata_path.write_text(metadata_content, encoding="utf-8")

    print("✅ Book project structure created successfully!")
    print("🛠️  pyproject.toml and full_export_book.py updated.")
    print("📁 Image generation template saved at scripts/data/image_prompt_generation_template.json")
    print("📄 Metadata saved to config/metadata.yaml")


if __name__ == "__main__":
    main()
