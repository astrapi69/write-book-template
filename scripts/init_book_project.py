import os
import json
from pathlib import Path

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

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
        "scripts/data"  # for image config JSON
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
    write_metadata_yaml(base / "config/metadata.yaml")
    write_metadata_json(base / "config/metadata_values.json")
    write_image_prompt_generation_template(base / "scripts/data/image_prompt_generation_template.json")

    print("✅ Book project structure created successfully!")
    print("📁 Image generation template saved at scripts/data/image_prompt_generation_template.json")
    print("ℹ️  You can edit config/metadata_values.json and run the metadata script (scripts/update_metadata_values.py) to populate metadata.yaml automatically.")

if __name__ == "__main__":
    main()
