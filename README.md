# 📚 Write-Book-Template

This repository is a ready-to-use template for efficiently writing, organizing, and publishing books with modern
tooling. It includes a structured directory layout, powerful automation scripts, and full integration
with [Poetry](https://python-poetry.org/) via a `pyproject.toml` configuration.

Authors can easily create, format, and export books in multiple formats like PDF, EPUB, MOBI, and DOCX.

---

## ✨ Features

- 📂 **Structured Directory:** Predefined folders for chapters, front matter, back matter, and assets
- 📝 **Markdown-Based Writing:** Compose in Markdown for clarity and compatibility
- 🔄 **Automated Conversion:** Generate multiple output formats via Pandoc
- 📜 **Dynamic Table of Contents:** Keep your structure organized and current
- 📑 **Metadata Automation:** Easily inject book metadata with a script
- 🚀 **Git Integration:** Seamless GitHub usage for versioning and collaboration
- 🧰 **Poetry Integration:** Dependency and script management powered by Poetry

---

## 🚦 Getting Started

### 1️⃣ Create Your Book Repository from this Template

- Click on the green **`Use this template`** button at the top of this repository page.
- Choose **`Create a new repository`** and name your book project.
- Clone it locally:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_BOOK_REPO.git
cd YOUR_BOOK_REPO
```

* * *

### 2️⃣ Initialize Project Structure

> ⚠️ **Note:** The shell script `scripts/create_project_structure.sh` is now **deprecated** and will be removed in the future.  
> ✅ Please use the **Python script with Poetry integration** instead.

Run the following command to create the complete folder structure and all required files:

```bash
poetry run init-book-project
```

This will:

* Create all necessary folders (`manuscript/`, `config/`, `assets/`, `output/`, etc.)
    
* Generate chapter and front/back matter files
    
* Create `metadata.yaml` and `metadata_values.json` with placeholders
    
* Add a template for image generation prompts (`scripts/data/image_project_config.json`)
    
* Prepare the project for exporting and translation
    

📘 **Full guide available here:**  
👉 [📦 Project Initialization – Wiki](https://github.com/astrapi69/write-book-template/wiki/Project-Initialization)

---

## ⚙️ Poetry-Based Setup

This project is configured with **Poetry**. To install dependencies and use the automation scripts:

```bash
poetry install
```

Available scripts (defined in `pyproject.toml`):

- `poetry run update-metadata-values` – injects structured metadata into your YAML file
- `poetry run full-export` – exports your book to multiple formats
- `poetry run print-version-build` – prints current version/build info

---

### 3️⃣ Automate Metadata Population

Replace placeholders in `config/metadata.yaml` using this command:

```bash
poetry run update-metadata-values
```
> This method ensures your virtual environment is used correctly and dependencies are managed by Poetry.

---

#### What the script does:

- Loads metadata values from `config/metadata_values.json`
- Replaces all placeholders like `{{BOOK_TITLE}}` in `metadata.yaml` with actual content
- Properly formats lists such as `KEYWORDS` and `OUTPUT_FORMATS` to YAML list syntax
- Automatically deletes the `metadata_values.json` file after successful population
- Logs success and error messages to the console

> 📘 Learn how this works in detail in the [Medium article](https://asterios-raptis.medium.com/automate-book-metadata-with-markdown-pandoc-ab78c03f58db)

### 4️⃣ Example Metadata Structure

After running the Python script, `metadata.yaml` will look like this:

```yaml
title: "Your Book Title"
subtitle: "A short subtitle describing your book"
author: "Your Name"
isbn: "Your ISBN Number"
edition: "Your Edition (e.g., 1st Edition, 2nd Edition)"
publisher: "Your Publisher Name"
date: "YYYY-MM-DD"
language: "en"
description: "Provide a detailed description of your book."
keywords:
  - "AI"
  - "machine learning"
  - "automation"
cover_image: "assets/covers/cover.jpg"
output_formats:
  - "pdf"
  - "epub"
  - "mobi"
kdp_enabled: true
```

### 5️⃣ Convert the Book to PDF/EPUB/MOBI

Once your book is written, export it:

```bash
poetry run full-export
```

The generated files will be available in the `output/` folder.

---

### 7️⃣ Push to GitHub

Commit and push your changes manually to GitHub:

```bash
git add .
git commit -m "Add new content or update chapters"
git push
```

---
## ✍️ Start Writing

- Add chapters in `manuscript/chapters/`
- Edit `manuscript/front-matter/toc.md` for your table of contents
- Add illustrations or diagrams under `assets/`

## 📖 Documentation

Helpful wiki pages to support every step of your book writing workflow:

- [📚 Home (Wiki Overview)](https://github.com/astrapi69/write-book-template/wiki)
- [✍️ How to Write a Book](https://github.com/astrapi69/write-book-template/wiki/How-to-Write-a-Book)
- [🛠 Generate Project Structure](https://github.com/astrapi69/write-book-template/wiki/Generate-Project-Structure)
- [📦 Automatically Export Book](https://github.com/astrapi69/write-book-template/wiki/Automatically-Export-Book)
- [🧠 Translate Markdown with DeepL](https://github.com/astrapi69/write-book-template/wiki/Translate-Markdown-with-DeepL)
- [💡 Translate with LM‐Studio](https://github.com/astrapi69/write-book-template/wiki/Translate-with-LM%E2%80%90Studio)
- [⚡ Shortcuts (Common Commands)](https://github.com/astrapi69/write-book-template/wiki/Shortcuts)
- [📘 Medium article: Automate Book Metadata](https://asterios-raptis.medium.com/automate-book-metadata-with-markdown-pandoc-ab78c03f58db)

---

## 📁 Directory Structure

```
write-book-template/
│── manuscript/
│   ├── chapters/
│   │   ├── 01-introduction.md
│   │   ├── 02-chapter.md
│   │   ├── ...
│   ├── front-matter/
│   │   ├── toc.md
│   │   ├── preface.md
│   │   ├── foreword.md
│   │   ├── acknowledgments.md
│   ├── back-matter/
│   │   ├── about-the-author.md
│   │   ├── appendix.md
│   │   ├── bibliography.md
│   │   ├── faq.md
│   │   ├── glossary.md
│   │   ├── index.md
│   ├── figures/
│   │   ├── fig1.png
│   │   ├── fig2.svg
│   │   ├── ...
│   ├── tables/
│   │   ├── table1.csv
│   │   ├── table2.csv
│   │   ├── ...
│   ├── references.bib  # If using citations (e.g., BibTeX, APA, MLA formats supported)
│── assets/ # Images, media, illustrations (for book content, cover design, and figures)
│   ├── covers/
│   │   ├── cover-design.png
│   ├── figures/
│   │   ├── diagrams/
│   │   ├── infographics/
│── config/ # Project configuration (metadata, styling, and optional Pandoc settings)
│   ├── metadata.yaml   # Title, author, ISBN, etc. (used for all formats: PDF, EPUB, MOBI)
│   ├── styles.css      # Custom styles for PDF/eBook
│   ├── template.tex    # LaTeX template (if needed)
│── output/             # Compiled book formats
│   ├── book.pdf
│   ├── book.epub
│   ├── book.mobi
│   ├── book.docx
│── scripts/ # Scripts and tools (initialize project, convert book, update metadata, and export formats)
│   ├── convert_book.sh                # Converts Markdown to multiple formats
│   ├── convert_img_tags.sh            # Converts the paths of the img tags
│   ├── convert_to_absolute.sh         # Converts the relative paths to absolute paths of the md images
│   ├── convert_to_relative.sh         # Converts back the absolute paths to relative paths of the md images
│   ├── create_project_structure.sh    # Initializes project structure
│   ├── full_export_book.py            # Exports book to all publishing formats with backup
│   ├── metadata_values_example.json   # example metadata values json file
│   ├── update_metadata_values.py      # Automates metadata population
│── LICENSE                                   # If open-source
│── pyproject.toml                            # Configuration file for poetry
│── README.md                                 # Project description
```

---

## 🎨 Customization

- **Metadata:** Modify `config/metadata.yaml` to personalize your book details (title, author, etc.)
- **Styles:** Edit `config/styles.css` to tailor your book’s appearance and formatting.
- **Scripts:** Customize conversion settings and output options as needed.

---

## 🛠 Requirements

- [Poetry](https://python-poetry.org/) (for managing this Python project)
- Python 3.x (for advanced automation with `full_export_book.py`)
- [Pandoc](https://pandoc.org/installing.html) for manuscript conversion.
- [Calibre](https://calibre-ebook.com/download) specifically for MOBI conversions.
- [GitHub CLI (`gh`)](https://cli.github.com/) for managing repositories (optional but recommended).

---

## ⚠️ Troubleshooting

Refer
to [Full Export Documentation](https://github.com/astrapi69/write-book-template/wiki/Automatically-Export-Book#%EF%B8%8F-troubleshooting)
for detailed error handling and solutions regarding export scripts.

---

## 🤝 Contributing

Found a bug or want to contribute? Pull requests and suggestions are welcome!

---

## 📄 License

Released under the MIT License. Please see the `LICENSE` file for details.

---

🚀 **Happy writing! Start your book today!**
