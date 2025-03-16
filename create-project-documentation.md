# Overview

For writing a book, an organized directory structure helps manage content, references, and publishing formats efficiently. Below is a recommended structure:

```
book-project/
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
│── assets/             # Images, media, illustrations (for book content, cover design, and figures)
│   ├── covers/
│   │   ├── cover-design.png
│   ├── figures/
│   │   ├── diagrams/
│   │   ├── infographics/
│── config/             # Project configuration (metadata, styling, and optional Pandoc settings)
│   ├── metadata.yaml   # Title, author, ISBN, etc. (used for all formats: PDF, EPUB, MOBI)
│   ├── styles.css      # Custom styles for PDF/eBook
│   ├── template.tex    # LaTeX template (if needed)
│── output/             # Compiled book formats
│   ├── book.pdf
│   ├── book.epub
│   ├── book.mobi
│── scripts/                        # Scripts and tools (initialize project, convert book, update metadata, and export formats)
│   ├── create_project_structure.sh # Initializes project structure
│   ├── convert_book.sh             # Converts Markdown to multiple formats
│   ├── full-export-book.py         # Exports book to all publishing formats with backup
│   ├── update-metadata-values.py   # Automates metadata population
│── README.md           # Project description
│── LICENSE             # If open-source
```

---

## 📜 Explanation

1. **`manuscript/`**
   * Holds the core book content, organized into subdirectories: `chapters/`, `front-matter/`, and `back-matter/`.
   * Use **Markdown (`.md`)** or **LaTeX (`.tex`)** for easy formatting and portability.
2. **`assets/`**
   * Stores images, figures, tables, and any media files.
3. **`config/`**
   * Includes metadata (`metadata.yaml`) and styling details for formatting the book.
4. **`output/`**
   * Contains exported book versions like **PDF, EPUB, MOBI**.
5. **`scripts/`**
   * Holds scripts for:
      - **Creating the project structure (`create_project_structure.sh`)**
      - **Converting Markdown to book formats (`convert_book.sh`)**
      - **Automating metadata population (`update-metadata-values.py`)**
      - **Full book export with backup (`full-export-book.py`)**
6. **`README.md` & `LICENSE`**
   * Provide information about the project and licensing details.

---

## 📖 Automating Book Metadata Population

The `update-metadata-values.py` script ensures that placeholders in `metadata.yaml` are replaced with actual values.

### 🔹 **Run the script:**
```bash
python scripts/update-metadata-values.py
```
This will:
- Fill in `metadata.yaml` with structured data.
- Ensure proper formatting for the **keywords array** in YAML.

---

## 📚 Converting Markdown to Different Book Formats

To convert the book from Markdown to **PDF, EPUB, and MOBI**, use:
```bash
bash scripts/convert_book.sh
```
This script will:
- Merge all chapters into a single document.
- Convert the manuscript to various formats using **Pandoc**.
- Ensure metadata is applied correctly from `metadata.yaml`.

### 🔹 **Requirements:**
- **Pandoc** (for conversion):
  ```bash
  sudo apt install pandoc
  ```
- **Calibre** (for MOBI conversion):
  ```bash
  sudo apt install calibre
  ```

---

## 🎯 Conclusion
This setup provides a **structured workflow** for book projects, supporting **manual input** and **AI automation**. 🚀

