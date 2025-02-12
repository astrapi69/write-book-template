# How to Write a New Book - A Step-by-Step Guide

This guide provides a structured approach to starting a new book project using the provided scripts. Follow these steps to set up your project, write content, and generate various book formats.

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

This will create a folder `book-project/` with the following structure:

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
│── tools/
│── README.md
│── LICENSE
```

---

## 3. Write Your Book
1. Open the `manuscript/chapters/` folder.
2. Add content to each chapter as separate markdown (`.md`) files.
3. Start with `01-introduction.md` and continue adding chapters incrementally.

Each markdown file should use simple syntax:
```markdown
# Chapter Title

This is the introduction to my book.

## Section 1
Some content here...
```

For referencing images, place them in `assets/figures/` and link them like this:
```markdown
![Figure 1](../assets/figures/example.png)
```

---

## 4. Add Metadata
Edit the file `config/metadata.yaml` to include book information:
```yaml
title: "My Awesome Book"
author: "Your Name"
isbn: "123-456-789"
date: "2025"
```

---

## 5. Generate Your Book (PDF, EPUB, MOBI)
Run the conversion script to compile the book:
```bash
chmod +x convert_book.sh
./convert_book.sh
```

This will generate:
```
output/
│── book.pdf
│── book.epub
│── book.mobi (if Calibre is installed)
```

---

## 6. Preview and Edit
- Open `output/book.pdf` for a preview.
- Modify content in `manuscript/chapters/` as needed.
- Re-run `convert_book.sh` to regenerate outputs.

---

## 7. Publish Your Book
Once you're satisfied:
- **Print it:** Upload `book.pdf` to a printing service like Amazon KDP.
- **Ebooks:** Upload `book.epub` and `book.mobi` to Kindle Direct Publishing or other platforms.

---

## 8. Additional Book Sections
Books can include various additional sections to enhance readability and organization:
- **Table of Contents (TOC):** A structured list of chapters and sections for easy navigation.
- **Preface:** An introduction by the author explaining why the book was written.
- **Acknowledgments:** A section to thank contributors and supporters.
- **Foreword:** A short piece written by someone other than the author, providing context or credibility.
- **Glossary:** A list of important terms and definitions used in the book.
- **FAQ (Frequently Asked Questions):** Answers to common questions related to the book’s topic.
- **Appendix:** Additional material that complements the main content, such as technical details or reference tables.
- **Bibliography:** A list of sources and references used.
- **Index:** A structured list of terms and topics covered in the book for easy navigation.
- **About the Author:** A section that provides information about the author, including background, achievements, and other works.

---

## 9. Writing a New Chapter
When adding a new chapter to your book, follow these steps:
1. **Create a new markdown file** in the `manuscript/chapters/` folder, following the naming convention (`03-new-chapter.md`).
2. **Update the Table of Contents (`toc.md`)** to reflect the new chapter title and its section structure.
3. **Ensure correct order** by placing the new chapter in sequence within `convert_book.sh`.
4. **Include necessary references** (e.g., images, citations) in the `assets/` or `manuscript/references.bib`.
5. **Check formatting** to ensure it aligns with the rest of the book.
6. **Regenerate the book** using `./convert_book.sh` to include the new content.

---

## 10. How the Book is Compiled
The `convert_book.sh` script compiles all the book sections in the correct order:
1. **Front Matter:** `toc.md`, `foreword.md`, `preface.md`, `acknowledgments.md`
2. **Main Content:** `chapters/*.md` (all chapters)
3. **Back Matter:** `appendix.md`, `glossary.md`, `faq.md`, `bibliography.md`, `index.md`, `about-the-author.md`

To ensure everything is compiled properly, run:
```bash
./convert_book.sh
```

---

## 11. Keep Writing!
Writing is an iterative process. Keep refining your book until it’s ready for publishing!

---

🎉 **Congratulations! You are now ready to write and publish your book!** 🚀

