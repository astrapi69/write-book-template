# Write-Book-Template

This repository serves as a template for writing and organizing books efficiently. It includes structured folders, scripts for automation, and guidelines to help authors create, format, and publish their books in multiple formats such as PDF, EPUB, and MOBI.

---

## Features
- 📂 **Structured Directory:** Organized folders for chapters, front matter, and back matter.
- 📝 **Markdown-Based Writing:** Write content in Markdown for easy formatting and conversion.
- 🔄 **Automated Conversion:** Convert your book to PDF, EPUB, and MOBI using Pandoc.
- 📜 **Table of Contents:** Maintain an updated TOC for structured navigation.
- 📑 **Additional Sections:** Support for glossary, index, bibliography, and more.
- 🚀 **Git Integration:** Easily push updates to GitHub and collaborate with others.

---

## Getting Started

### 1️⃣ Clone the Template Repository
```bash
git clone https://github.com/YOUR_USERNAME/write-book-template.git
cd write-book-template
```

### 2️⃣ Set Up Your Book Repository
Run the setup script to initialize a new book project:
```bash
chmod +x create_project_structure.sh
./create_project_structure.sh
```
This will generate the necessary folders and files.

### 3️⃣ Start Writing
- Navigate to `manuscript/chapters/` and begin writing your book in Markdown.
- Update `manuscript/front-matter/toc.md` to reflect new chapters.
- Use `assets/` for storing images and figures.

### 4️⃣ Convert to PDF, EPUB, and MOBI
Run the script to generate different book formats:
```bash
chmod +x convert_book.sh
./convert_book.sh
```
Output files will be stored in the `output/` directory.

### 5️⃣ Push to GitHub
Use the Git automation script to set up and push your book project:
```bash
chmod +x setup_github_repo.sh
./setup_github_repo.sh
```

---

## Directory Structure
```
write-book-template/
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

## Customization
- Edit `config/metadata.yaml` to update book details.
- Modify `config/styles.css` to change the book’s appearance.
- Adjust `convert_book.sh` to customize output formats.

---

## Requirements
- [Pandoc](https://pandoc.org/installing.html) for format conversion.
- [Calibre](https://calibre-ebook.com/download) for MOBI conversion.
- GitHub CLI (`gh`) for repository management (optional).

---

## Contributing
Feel free to contribute by submitting issues or pull requests. Feedback and improvements are always welcome!

---

## License
This template is released under the MIT License. See `LICENSE` for more details.

🚀 **Start writing your book today!**
