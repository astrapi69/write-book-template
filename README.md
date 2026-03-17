# Write-Book-Template

This repository is a ready-to-use GitHub template for writing, organizing, and publishing books with modern tooling. It
provides a structured directory layout, configuration files, and a Makefile, with all automation powered by
the [manuscripta](https://github.com/astrapi69/manuscripta) library.

Authors can create, format, and export books in multiple formats: PDF, EPUB, DOCX, HTML, and Markdown.

---

## Features

- Structured directory layout for chapters, front matter, back matter, and assets
- Markdown-based writing for clarity and compatibility
- Multi-format export via Pandoc (PDF, EPUB, DOCX, HTML, Markdown)
- Print versions optimized for paperback and hardcover (KDP-ready)
- Audiobook generation with pluggable TTS engines
- Translation support via DeepL and LMStudio
- Manuscript validation and sanitization via [manuscript-tools](https://pypi.org/project/manuscript-tools/)
- All CLI tools provided by [manuscripta](https://github.com/astrapi69/manuscripta), no local scripts needed
- Pipeline updates via `poetry update`

---

## Getting Started

### 1. Create Your Book Repository from this Template

- Click on the green **`Use this template`** button at the top of this repository page.
- Choose **`Create a new repository`** and name your book project.
- Clone it locally:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_BOOK_REPO.git
cd YOUR_BOOK_REPO
```

---

### 2. Initialize Project Structure

```bash
make setup
```

This will install all dependencies and run the interactive project initializer, which creates the complete folder
structure and all required files.

Alternatively, step by step:

```bash
make lock-install
make init-bp
```

Full
guide: [Project Initialization (Wiki)](https://github.com/astrapi69/write-book-template/wiki/Project-Initialization)

---

### 3. Automate Metadata Population

Replace placeholders in `config/metadata.yaml`:

```bash
poetry run update-metadata-values
```

This loads metadata values from `config/metadata_values.json`, replaces all placeholders like `{{BOOK_TITLE}}`, formats
lists to YAML syntax, and deletes the JSON file after successful population.

---

### 4. Export Your Book

```bash
# Export all formats with cover
make export

# Single formats
make pdf
make ebook
make docx
make html
make markdown

# Print versions
make paperback
make hardcover

# Safe mode (fast drafts, no source modifications)
make ebook ARGS="--safe"
```

The generated files will be available in the `output/` folder.

---

### 5. Start Writing

- Add chapters in `manuscript/chapters/`
- Edit `manuscript/front-matter/toc.md` for your table of contents
- Add illustrations or diagrams under `assets/`

---

## Directory Structure

```text
write-book-template/
│── manuscript/
│   ├── chapters/
│   │   ├── 01-introduction.md
│   │   ├── 02-chapter.md
│   ├── front-matter/
│   │   ├── toc.md
│   │   ├── toc-print.md
│   │   ├── preface.md
│   │   ├── foreword.md
│   ├── back-matter/
│   │   ├── about-the-author.md
│   │   ├── acknowledgments.md
│   │   ├── appendix.md
│   │   ├── bibliography.md
│   │   ├── epilogue.md
│   │   ├── glossary.md
│   │   ├── imprint.md
│── assets/
│   ├── covers/
│   ├── images/
│   ├── fonts/
│   ├── templates/
│── config/
│   ├── metadata.yaml
│   ├── export-settings.yaml
│   ├── voice-settings.yaml
│── output/
│── pyproject.toml
│── Makefile
│── LICENSE
│── README.md
```

---

## Makefile Targets

Run `make help` for a full list. Key targets:

| Target                 | Description                                 |
|------------------------|---------------------------------------------|
| `make setup`           | Install dependencies and initialize project |
| `make export`          | Export all formats with cover               |
| `make pdf`             | Export PDF                                  |
| `make ebook`           | Export EPUB                                 |
| `make paperback`       | Export print version (paperback)            |
| `make hardcover`       | Export print version (hardcover)            |
| `make audiobook`       | Generate audiobook                          |
| `make translate-en-de` | Translate English to German (DeepL)         |
| `make ms-check`        | Run manuscript style checks                 |
| `make ms-validate`     | Full manuscript validation pipeline         |
| `make clean`           | Remove output and cache artifacts           |

Full documentation: [Makefile Overview (Wiki)](https://github.com/astrapi69/write-book-template/wiki/Makefile-Overview)

---

## Documentation

The full documentation is available in the [Wiki](https://github.com/astrapi69/write-book-template/wiki).

**Getting Started:**
[Home](https://github.com/astrapi69/write-book-template/wiki) |
[Project Initialization](https://github.com/astrapi69/write-book-template/wiki/Project-Initialization) |
[How to Write a Book](https://github.com/astrapi69/write-book-template/wiki/How-to-Write-a-Book) |
[Generate Project Structure](https://github.com/astrapi69/write-book-template/wiki/Generate-Project-Structure)

**Writing Tools:**
[Chapter File Generator](https://github.com/astrapi69/write-book-template/wiki/Chapter-File-Generator) |
[Generate Images](https://github.com/astrapi69/write-book-template/wiki/Generate-Images) |
[Restructure Chapters](https://github.com/astrapi69/write-book-template/wiki/Restructure-Chapters)

**Translation:**
[Translate with DeepL](https://github.com/astrapi69/write-book-template/wiki/Translate-Markdown-with-DeepL) |
[Translate with LM Studio](https://github.com/astrapi69/write-book-template/wiki/Translate-with-LM%E2%80%90Studio) |
[Translation CLI Commands](https://github.com/astrapi69/write-book-template/wiki/Translation-CLI-Commands-Shortcuts)

**Export:**
[Automatic Book Export](https://github.com/astrapi69/write-book-template/wiki/Automatically-Export-Book) |
[Export Shortcuts](https://github.com/astrapi69/write-book-template/wiki/Shortcuts-For-Export) |
[Export to EPUB 2](https://github.com/astrapi69/write-book-template/wiki/Export-to-EPUB-2) |
[Export HTML to PDF (KDP)](https://github.com/astrapi69/write-book-template/wiki/Exporting-HTML-Books-to-PDF-with-Puppeteer-(KDP-Ready))

**Audio:**
[Generate Audiobook](https://github.com/astrapi69/write-book-template/wiki/Generate-Audiobook)

---

## Customization

- **Metadata:** Modify `config/metadata.yaml` to personalize your book details
- **Export Settings:** Edit `config/export-settings.yaml` to change section order per book type
- **Voice Settings:** Edit `config/voice-settings.yaml` for audiobook TTS configuration

---

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management
- [Pandoc](https://pandoc.org/installing.html) for manuscript conversion

---

## Powered By

- [manuscripta](https://github.com/astrapi69/manuscripta) - Book production pipeline (export, translation, audiobook,
  project management)
- [manuscript-tools](https://pypi.org/project/manuscript-tools/) - Manuscript validation, sanitization, and metrics

---

## Troubleshooting

Refer to
the [Makefile Overview (Wiki)](https://github.com/astrapi69/write-book-template/wiki/Makefile-Overview#troubleshooting)
for common issues and solutions.

---

## Contributing

Found a bug or want to contribute? Pull requests and suggestions are welcome!

---

## License

Released under the MIT License. See the `LICENSE` file for details.
