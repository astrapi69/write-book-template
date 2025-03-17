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

### 📂 Customizing Project Structure
You can modify `create_project_structure.sh` to **add custom directories**. Example:

💡 **To add an "exercises" folder:**  
Edit `scripts/create_project_structure.sh` and add:
```bash

# Define directories
DIRECTORIES=(
    "$PROJECT_NAME/manuscript/exercises" # <= new added directory
    "$PROJECT_NAME/manuscript/chapters"
    "$PROJECT_NAME/manuscript/front-matter"
    "$PROJECT_NAME/manuscript/back-matter"
    "$PROJECT_NAME/manuscript/figures"
    "$PROJECT_NAME/manuscript/tables"
    "$PROJECT_NAME/assets/covers"
    "$PROJECT_NAME/assets/figures/diagrams"
    "$PROJECT_NAME/assets/figures/infographics"
    "$PROJECT_NAME/config"
    "$PROJECT_NAME/output"
)
```

📌 This will create a new **`exercises/` directory** inside the manuscript folder.

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

# 📖 **Metadata Configuration (`metadata.yaml`)**

The `metadata.yaml` file contains essential information about your book, including **title, author, publishing details, styling options, and export settings**. This file is crucial for **automating book generation**, ensuring consistency across formats (PDF, EPUB, MOBI), and preparing metadata for publishing platforms.

## **📌 Available Metadata Keys**
Below is a breakdown of the **supported metadata keys** in `metadata.yaml`:

### **1️⃣ Essential Book Information**
| **Key**       | **Type**   | **Description** |
|--------------|-----------|----------------|
| `title`      | `string`  | The book’s title. |
| `subtitle`   | `string`  | A short subtitle providing additional context. |
| `author`     | `string`  | The author's name. Multiple authors can be separated by commas. |
| `isbn`       | `string`  | The book’s ISBN number (if applicable). |
| `edition`    | `string`  | The edition of the book (e.g., `"1st Edition"`). |
| `publisher`  | `string`  | The name of the publisher or `"Self-Published"`. |
| `date`       | `string`  | Publication date in `YYYY-MM-DD` format. |
| `language`   | `string`  | The book's language code (`en`, `de`, `fr`, etc.). |
| `description` | `string` | A short summary of the book (used for publishing metadata). |
| `keywords`   | `list`    | A list of keywords for categorization (e.g., `["AI", "Machine Learning", "No-Code"]`). |

### **2️⃣ Formatting & Styling Options**
| **Key**         | **Type**   | **Description** |
|----------------|-----------|----------------|
| `cover_image`  | `string`  | Path to the cover image (e.g., `"assets/covers/cover.jpg"`). |
| `styles`       | `string`  | Path to a custom stylesheet (`config/styles.css`). |
| `template`     | `string`  | Path to a custom Pandoc/LaTeX template (`config/template.tex`). |
| `font`         | `string`  | Preferred font (used for PDF export). |
| `page_size`    | `string`  | Page format for PDFs (`A4`, `Letter`, etc.). |
| `margin`       | `string`  | Margin settings for print layout (e.g., `"1in"`). |

### **3️⃣ Content Structure Options**
| **Key**        | **Type**   | **Description** |
|--------------|-----------|----------------|
| `toc`        | `boolean` | `true` to generate a Table of Contents. |
| `bibliography` | `string` | Path to the bibliography file (`"manuscript/references.bib"`). |
| `appendix`   | `boolean` | `true` if an appendix is included. |
| `glossary`   | `boolean` | `true` to include a glossary section. |
| `index`      | `boolean` | `true` to generate an index at the end. |

### **4️⃣ Export & Publishing Options**
| **Key**          | **Type**   | **Description** |
|-----------------|-----------|----------------|
| `output_formats` | `list`    | Supported export formats (`["pdf", "epub", "mobi"]`). |
| `kdp_enabled`    | `boolean` | `true` if publishing on Amazon KDP. |
| `print_ready`    | `boolean` | `true` if the book is formatted for print. |

---

## **📂 Example `metadata.yaml`**
```yaml
title: "AI for Everyone: Crafting Prompts Without Coding Skills"
subtitle: "A beginner-friendly guide to AI prompt engineering"
author: "Asterios Raptis"
isbn: "979-8309899173"
edition: "2nd Edition"
publisher: "Asterios Raptis"
date: "2025-03-17"
language: "en"
description: "A comprehensive guide to using AI prompts effectively, designed for non-coders to enhance their productivity and creativity."
keywords:
  - "AI"
  - "artificial intelligence"
  - "prompt engineering"
  - "no-code AI"
  - "creative AI"
cover_image: "assets/covers/cover.jpg"
styles: "config/styles.css"
template: "config/template.tex"
font: "Times New Roman"
page_size: "A4"
margin: "1in"
toc: true
bibliography: "manuscript/references.bib"
appendix: true
glossary: false
index: true
output_formats:
  - "pdf"
  - "epub"
  - "mobi"
  - "docx"
kdp_enabled: true
print_ready: false
```

---

## **⚙️ Automating Metadata Population**
To **automatically populate `metadata.yaml`**, use the **`update-metadata-values.py`** script. This script loads values from `config/metadata_values.json` and updates placeholders in `metadata.yaml`.

### **🔹 1. Setup `metadata_values.json`**
Create a JSON file (`config/metadata_values.json`) with your book’s metadata:
```json
{
    "BOOK_TITLE": "AI for Everyone: Crafting Prompts Without Coding Skills",
    "BOOK_SUBTITLE": "A beginner-friendly guide to AI prompt engineering",
    "AUTHOR_NAME": "Asterios Raptis",
    "ISBN_NUMBER": "979-8309899173",
    "BOOK_EDITION": "2nd Edition",
    "PUBLISHER_NAME": "Asterios Raptis",
    "PUBLICATION_DATE": "2025-03-17",
    "LANGUAGE": "en",
    "BOOK_DESCRIPTION": "A comprehensive guide to using AI prompts effectively, designed for non-coders to enhance their productivity and creativity.",
    "KEYWORDS": ["AI", "artificial intelligence", "prompt engineering", "no-code AI", "creative AI"]
}
```

### **🔹 2. Run the Metadata Update Script**
```bash
python scripts/update-metadata-values.py
```

✅ This will:
- Load `metadata_values.json` and **replace placeholders** in `metadata.yaml`.
- Format **lists correctly** (e.g., `keywords` and `output_formats`).
- Ensure **boolean values** are converted to `true` or `false` as needed.

---

## **🛠 Error Handling in Scripts**

While running these scripts, some **errors may occur**:

### **Common Errors & Solutions**
| **Error** | **Cause** | **Solution** |
|-----------|----------|--------------|
| `FileNotFoundError` | Missing `metadata_values.json` | Ensure the file exists in `config/` |
| `Invalid JSON format` | Incorrectly formatted JSON file | Validate JSON using an online checker |
| `Pandoc not found` | Pandoc is not installed | Install using `sudo apt install pandoc` |

✅ **Basic error handling is implemented** in `update-metadata-values.py`, which warns users about missing or invalid files.

---

## 🎯 **Final Thoughts**
- ✅ **Metadata is fully customizable** via `metadata_values.json`.
- ✅ **Scripts ensure proper formatting** for metadata fields.
- ✅ **Supports AI automation**, making it easy to generate structured metadata dynamically.

This documentation update provides **full metadata flexibility** for book projects. 🚀

## 🎯 Conclusion
This setup provides a **structured workflow** for book projects, supporting **manual input** and **AI automation**. 🚀

