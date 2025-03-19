# Full Export Book Script Documentation

## 📚 Overview
The `full_export_book.py` script automates the export of a book into multiple formats (**Markdown, PDF, EPUB, DOCX**) using **Pandoc**.

### ✨ Features
👉 Converts **relative image paths** to **absolute paths** before export  
👉 Handles **both Markdown images (`![alt](path)`) and HTML `<img>` tags**  
👉 Exports book content into multiple formats using **Pandoc**  
👉 Converts **absolute paths back to relative paths** after export  
👉 Supports **custom arguments** for flexible execution  
👉 **Poetry integration**: Run via `poetry run full-export`

---

## ❓ Why Convert Paths to Absolute?
### 🔍 **The Problem**
Pandoc **does not always resolve relative paths correctly**, especially when exporting to:
- **PDF (via LaTeX)**
- **EPUB (due to internal resource handling)**
- **DOCX (for embedded images)**

Example **problematic image reference**:
```markdown
![Figure 1](../../assets/figures/diagram.png)
```
This may result in **broken references or missing images**.

### ✅ **The Solution**
Before export, the script **automatically converts** all image paths to **absolute paths**:
```markdown
![Figure 1](/absolute/path/to/assets/figures/diagram.png)
```
This ensures:
- **No missing images** in **PDF, EPUB, and DOCX**
- **Platform-independent behavior** (Windows, macOS, Linux)
- **Correct image embedding across formats**

After export, the script **restores relative paths** to keep the Markdown clean.

---

## 🚀 Installation & Requirements
### **1️⃣ Install Pandoc**
Ensure **Pandoc** is installed:  
🔗 [https://pandoc.org/installing.html](https://pandoc.org/installing.html)
```bash
pandoc --version
```

### **2️⃣ Install Python & Poetry**
Ensure **Python 3.13+** and **Poetry** are installed:
```bash
python3 --version
poetry --version
```
If Poetry is not installed:
```bash
pip install poetry
```

### **3️⃣ Install Dependencies**
Run:
```bash
poetry install
```

---

## 🛠 How to Use
### **1️⃣ Default Export (All Formats)**
```bash
poetry run full-export
```
This will:
- Convert images to **absolute paths**
- Compile the book into **Markdown, PDF, EPUB, and DOCX**
- Restore **relative paths** after export

---

### **2️⃣ Export Specific Formats**
Specify formats using `--format` (comma-separated):
```bash
poetry run full-export --format pdf,epub
```
**Available formats:**
- `markdown` (GitHub Flavored Markdown)
- `pdf`
- `epub`
- `docx`

Example: **Export only PDF and EPUB**
```bash
poetry run full-export --format pdf,epub
```

---

### **3️⃣ Skip Image Processing**
If images are already correctly linked, you can **skip image conversion**:
```bash
poetry run full-export --skip-images
```
🚀 **Use case:** Faster builds when testing content changes.

---

## 📃 Logs
All logs are saved in `export.log`.  
To view logs in real-time:
```bash
tail -f export.log
```
If errors occur, check `export.log` for debugging.

---

## 📂 Project Structure
```plaintext
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

## ⚠️ Troubleshooting
### **1️⃣ Pandoc Not Found**
If you see:
```bash
Command 'pandoc' not found
```
Install Pandoc:
```bash
sudo apt install pandoc  # Ubuntu/Debian
brew install pandoc  # macOS
choco install pandoc  # Windows
```

### **2️⃣ Images Not Found in PDF/EPUB**
- Ensure images exist in `assets/`
- Try running with **absolute paths enabled**:
  ```bash
  poetry run full-export
  ```
- Verify image paths inside your Markdown files.

### **3️⃣ Pandoc Metadata Warning**
If you see:
```
[WARNING] This document format requires a nonempty <title> element.
```
Ensure `config/metadata.yaml` exists.  
If missing, the script will **automatically generate** a default one.

---

## 🎉 Final Notes
This script **automates the entire export process**, making it easy for any user to generate a **professional-quality book**! 📚🌟

For any issues, check `export.log` or open an issue in the repository.

---

### ✅ **This version:**
✔ **Includes all recent improvements**  
✔ **Optimized for flexibility**  
✔ **Fully compatible with `write-book-template`**  
✔ **Works seamlessly with Poetry**

🚀 **Now ready for use in any book project!** 🚀  

