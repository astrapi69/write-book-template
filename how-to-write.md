# How to Write a Book: Step-by-Step Guide

This guide provides a structured approach to starting a new book project using provided scripts. Follow these steps to set up your project, write content, and generate various book formats.

---

## 1. Install Required Software
Before you start, install the necessary tools:

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install pandoc calibre
```

### macOS (using Homebrew)

```bash
brew install pandoc calibre
```

### Windows

- Install **[Pandoc](https://pandoc.org/installing.html)**
- Install **[Calibre](https://calibre-ebook.com/download)**
- Use Git Bash or WSL for running scripts

---

## 2. Create a New Book Project
Run the following script to generate a structured project directory:

```bash
chmod +x create_project_structure.sh
./create_project_structure.sh
```

This will create:

```
book-project/
│── manuscript/
│   ├── chapters/
│   │   ├── 01-introduction.md
│   │   ├── 02-chapter-title.md
│   ├── front-matter/
│   │   ├── toc.md
│   │   ├── preface.md
│   │   ├── acknowledgments.md
│   │   ├── foreword.md
│   ├── back-matter/
│   │   ├── appendix.md
│   │   ├── glossary.md
│   │   ├── faq.md
│   │   ├── bibliography.md
│   │   ├── index.md
│   │   ├── about-the-author.md
│── assets/
│── config/
│── output/
│── README.md
│── LICENSE
```

---

## 3. Write Your Book

- Create or edit markdown files in `manuscript/chapters/`
- Add your content chapter-by-chapter.

Example:

```
manuscript/chapters/01-introduction.md
```

---

## 4. Add Metadata and Style
Edit `config/metadata.yaml` and `config/styles.css` to customize your book's metadata and style.

Example metadata:

```yaml
title: "My Awesome Book"
author: "Your Name"
date: "2025"
isbn: "123-4567890123"
```

---

## 5. Generate Book Formats

Use the preferred script:

- Recommended (robust and flexible): [`full_export_book.py`](#documentation-for-full-export-bookpy)

Run the script:

```bash
python full_export_book.py
```

Outputs will be in the `output/` directory:

- PDF
- EPUB
- DOCX
- Markdown

---

## 6. Preview and Edit
- Open `output/book.pdf` for a preview.
- Modify content in `manuscript/chapters/` as needed.
- Re-run the export script to regenerate outputs.

---

## 7. Publish Your Book
Once you're satisfied:
- **Print it:** Upload `book.pdf` to a printing service like Amazon KDP.
- **Ebooks:** Upload `book.epub` and `book.mobi` to Kindle Direct Publishing or other platforms.

---

## 8. Additional Book Sections
Enhance your book readability by adding:
- **Preface, Acknowledgments, Epilogue**
- **Glossary, Bibliography, Appendix**
- **Index, About the Author**

---

For detailed usage of the export script, see the [documentation for `full_export_book.py`](full-export-documentation.md).

---

🎉 **Congratulations! You are now ready to publish your book!** 🚀

