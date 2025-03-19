# 📚 Write-Book-Template

This repository is a convenient template for efficiently writing and organizing books. It features structured directories, automation scripts, and clear guidelines to help authors easily create, format, and publish their books in popular formats such as PDF, EPUB, and MOBI.

---

## ✨ Features

- 📂 **Structured Directory:** Clearly organized folders for chapters, front matter, and back matter
- 📝 **Markdown-Based Writing:** Write your content using Markdown for straightforward formatting and conversion
- 🔄 **Automated Conversion:** Convert your manuscript to PDF, EPUB, and MOBI formats effortlessly with Pandoc
- 📜 **Dynamic Table of Contents:** Maintain an up-to-date TOC for structured navigation
- 📑 **Additional Sections:** Built-in support for glossary, index, bibliography, appendix, and FAQ
- 🚀 **Git Integration:** Seamlessly manage updates, collaborate, and share your work via GitHub

---

## 🚦 Getting Started

### 1️⃣ Create Your Book Repository from this Template

- Click on the green **`Use this template`** button at the top of this repository page.
- Choose **`Create a new repository`**.
- Enter a name for your new book repository and complete the setup.

Then, clone your newly created repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_BOOK_REPO.git
cd YOUR_BOOK_REPO
```

### 2️⃣ Initialize Your Book Project

Run the Bash script to set up the required directory structure:
```bash
bash scripts/create_project_structure.sh
```
This will:
- Create the necessary folders for chapters, metadata, assets, and configuration.
- Generate `metadata.yaml` with placeholders for customization.

After execution, update `metadata.yaml` manually or use automation.

### 3️⃣ Automate Metadata Population
To replace placeholders in `metadata.yaml`, use the Python script:
```bash
python scripts/update_metadata_values.py
```
This script:
- Loads metadata values from `config/metadata_values.json`.
- Replaces placeholders in `metadata.yaml` with structured values.
- Ensures correct formatting for **lists** like `keywords` and `output_formats`.

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

Once the manuscript is ready, use **Pandoc** for conversion:

```bash
pandoc output/merged_book.md -o output/book.pdf --metadata-file=config/metadata.yaml
pandoc output/merged_book.md -o output/book.epub --metadata-file=config/metadata.yaml
```

Converted files will be available in the `output/` directory.

### 6️⃣ Start Writing

- Navigate to `manuscript/chapters/` and start writing your chapters in Markdown.
- Update `manuscript/front-matter/toc.md` to reflect your chapters and content.
- Store your images and figures in the `assets/` folder.

### 7️⃣ Push to GitHub

Commit and push your changes manually to GitHub:

```bash
git add .
git commit -m "Add new content or update chapters"
git push
```

---

## 📖 Documentation

Detailed guides and documentation to support your book writing process:

- [wiki](https://github.com/astrapi69/write-book-template/wiki)
- [How to Write a Book: Step-by-Step Guide](how-to-write.md)
- [Full Export Documentation](full-export-documentation.md)
- [Create Project Structure Documentation](create-project-documentation.md)

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
│── create-project-documentation.md           # Documentation for generate the project structure
│── full-export-documentation.md              # Documentation the export
│── how-to-write.md                           # Documentation how to use the project structure and save the files
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

- [Pandoc](https://pandoc.org/installing.html) for manuscript conversion.
- [Calibre](https://calibre-ebook.com/download) specifically for MOBI conversions.
- [GitHub CLI (`gh`)](https://cli.github.com/) for managing repositories (optional but recommended).
- Python 3.x (for advanced automation with `full_export_book.py`)

---

## ⚠️ Troubleshooting

Refer to [Full Export Documentation](full-export-documentation.md#troubleshooting) for detailed error handling and solutions regarding export scripts.

---

## 🤝 Contributing

Contributions are warmly welcomed! Feel free to submit issues, suggestions, or pull requests to help improve this template.

---

## 📄 License

Released under the MIT License. Please see the `LICENSE` file for details.

---

🚀 **Happy writing! Start your book today!**
