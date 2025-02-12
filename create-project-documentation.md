# Overview

For writing a book, an organized directory structure helps manage content, references, and publishing formats efficiently. Below is a recommended structure:

```
book-project/
│── manuscript/
│   ├── chapters/
│   │   ├── 01-introduction.md
│   │   ├── 02-chapter-title.md
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
│   ├── references.bib  # If using citations
│── assets/             # Images, media, illustrations
│   ├── covers/
│   │   ├── cover-design.png
│   ├── figures/
│   │   ├── diagrams/
│   │   ├── infographics/
│── config/             # Project configuration
│   ├── metadata.yaml   # Title, author, ISBN, etc.
│   ├── styles.css      # Custom styles for PDF/eBook
│   ├── template.tex    # LaTeX template (if needed)
│── output/             # Compiled book formats
│   ├── book.pdf
│   ├── book.epub
│   ├── book.mobi
│── tools/              # Scripts and tools
│   ├── build.sh        # Script to compile book
│   ├── convert.py      # Conversion scripts
│── README.md           # Project description
│── LICENSE             # If open-source
```

### Explanation:

1. **`manuscript/`**

    * Holds the core book content, organized into subdirectories: `chapters/`, `front-matter/`, and `back-matter/`.
    * Use **Markdown (`.md`)** or **LaTeX (`.tex`)** for easy formatting and portability.
2. **`assets/`**

    * Stores images, figures, tables, and any media files.
3. **`config/`**

    * Includes metadata and styling details for formatting the book.
4. **`output/`**

    * Contains exported book versions like **PDF, EPUB, MOBI**.
5. **`tools/`**

    * Holds scripts for building and converting the book to different formats.
6. **`README.md` & `LICENSE`**

    * Provide information about the project and licensing details.

# create an automated script to convert Markdown to different book formats (PDF, EPUB, MOBI)

Here are two scripts:

1. **`create_project_structure.sh`** – This script initializes the book project structure.
2. 
2. **`convert_book.sh`** – This script converts the book from Markdown to multiple formats (PDF, EPUB, MOBI) using Pandoc.

* * *

### 1️⃣ **Script to Create the Project Structure (`create_project_structure.sh`)**

This script sets up the book project directory.

```bash
#!/bin/bash

# Set project name
PROJECT_NAME="book-project"

# Define directories
DIRECTORIES=(
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
    "$PROJECT_NAME/tools"
)

# Create directories
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
done

# Create sample files
touch "$PROJECT_NAME/manuscript/chapters/01-introduction.md"
touch "$PROJECT_NAME/manuscript/chapters/02-chapter-title.md"
touch "$PROJECT_NAME/manuscript/front-matter/preface.md"
touch "$PROJECT_NAME/manuscript/back-matter/appendix.md"
touch "$PROJECT_NAME/manuscript/references.bib"
touch "$PROJECT_NAME/config/metadata.yaml"
touch "$PROJECT_NAME/config/styles.css"
touch "$PROJECT_NAME/README.md"
touch "$PROJECT_NAME/LICENSE"

echo "# Book Project" > "$PROJECT_NAME/README.md"
echo "This is the book project structure." >> "$PROJECT_NAME/README.md"

echo "✅ Book project structure created successfully!"
```

📌 **Usage:** Save the script as `create_project_structure.sh`, then run:

```bash
chmod +x create_project_structure.sh
./create_project_structure.sh
```

* * *

### 2️⃣ **Script to Convert the Book (`convert_book.sh`)**

This script converts the book's Markdown files into **PDF, EPUB, and MOBI** formats using **Pandoc**.

```bash
#!/bin/bash

# Define variables
BOOK_NAME="book"
INPUT_DIR="manuscript/chapters"
OUTPUT_DIR="output"
METADATA="config/metadata.yaml"
STYLE="config/styles.css"

# Ensure Pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc is not installed. Install it using: sudo apt install pandoc"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Merge all markdown chapters into a single file
cat $INPUT_DIR/*.md > "$OUTPUT_DIR/$BOOK_NAME.md"

# Convert to PDF
pandoc "$OUTPUT_DIR/$BOOK_NAME.md" --metadata-file=$METADATA -o "$OUTPUT_DIR/$BOOK_NAME.pdf" --css=$STYLE

# Convert to EPUB
pandoc "$OUTPUT_DIR/$BOOK_NAME.md" --metadata-file=$METADATA -o "$OUTPUT_DIR/$BOOK_NAME.epub"

# Convert to MOBI (requires kindlegen or Calibre's ebook-convert)
if command -v ebook-convert &> /dev/null; then
    ebook-convert "$OUTPUT_DIR/$BOOK_NAME.epub" "$OUTPUT_DIR/$BOOK_NAME.mobi"
else
    echo "⚠️ MOBI conversion skipped. Install Calibre and use: sudo apt install calibre"
fi

echo "✅ Book converted successfully! Find the files in the '$OUTPUT_DIR' directory."
```

📌 **Usage:** Save the script as `convert_book.sh`, then run:

```bash
chmod +x convert_book.sh
./convert_book.sh
```

* * *

### **Requirements for Conversion Script**

* Install **Pandoc**:

    ```bash
    sudo apt install pandoc
    ```

* Install **Calibre (optional, for MOBI conversion)**:

    ```bash
    sudo apt install calibre
    ```


Would you like any modifications or additions to the scripts? 🚀