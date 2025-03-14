## Documentation for `full-export-book.py`

### Overview

`full-export-book.py` automates the process of converting markdown files into multiple e-book formats suitable for Kindle Direct Publishing (KDP). It supports PDF, EPUB, DOCX, and Markdown compilation through Pandoc.

### Features:

- **Automatic Backup:**
    - Checks if the output directory exists, and if it does, creates a backup of the previous compilation to prevent data loss.

- **Structured File Handling:**
    - Collects markdown files from predefined directories:
        - Front Matter (title, table of contents, foreword, preface)
        - Chapters (sorted automatically)
        - Back Matter (epilogue, glossary, etc.)

- **Multi-Format Support:**
    - Supports compiling markdown files to:
        - PDF (using pdflatex)
        - EPUB
        - DOCX
        - Markdown

- **Flexible Formatting:**
    - Inserts appropriate page breaks and formatting based on the target file format.

---

### Required Directory Structure:
```
project-root/
├── BOOK_DIR/
│   ├── front-matter/
│   │   ├── book-title.md
│   │   ├── toc.md
│   │   ├── foreword.md
│   │   └── preface.md
│   ├── chapters/
│   │   ├── chapter-1.md
│   │   ├── chapter-2.md
│   │   └── ...
│   └── back-matter/
│       ├── epilogue.md
│       ├── glossary.md
│       ├── bibliography.md
│       └── ...
├── OUTPUT_DIR/ (auto-generated)
└── BACKUP_DIR/ (created automatically during backup)
```

---

### How to Use:

Run the script from the command line:
```bash
python full-export-book.py
```

### Prerequisites:
- Python 3.x
- Pandoc installed and accessible from command line
    - For PDF generation, LaTeX engine (like pdflatex) is required.

### Variables to configure within the script:

- `BOOK_DIR`: Source directory containing markdown files.
- `OUTPUT_DIR`: Directory for compiled book outputs.
- `BACKUP_DIR`: Directory to store backups.

### Output:
Upon successful execution, compiled book files are available in the specified `OUTPUT_DIR`.

---

### Troubleshooting:

- **Missing Files:**
    - Ensure all markdown sections exist in their directories as outlined.
- **Pandoc Errors:**
    - Verify Pandoc and LaTeX installations, if needed.

---

**Recommended Usage:**
This script is ideal for automating and maintaining consistent exports of manuscripts, especially for repeated or iterative publishing processes, such as Kindle Direct Publishing.

