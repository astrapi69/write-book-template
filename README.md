
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
- Generate `metadata.yaml` with placeholders.

After execution, update `metadata.yaml` manually or use automation.

### 3️⃣ Updating Metadata Automatically
To replace placeholders in `metadata.yaml`, use the Python script:
```bash
python scripts/update-metadata-values.py
```
This script:
- Fills in `metadata.yaml` with structured data with the values in the script.
- Ensures correct formatting for the **keywords array**.

### 4️⃣ Example Metadata Structure
After running the Python script, `metadata.yaml` will look like this:
```yaml
title: "Enter the title of your book"
subtitle: "Enter a short subtitle describing your book"
author: "Enter the author's full name"
isbn: "Enter the ISBN number (if available)"
edition: "Enter the edition of the book (e.g., 1st Edition, 2nd Edition)"
publisher: "Enter the publisher's name"
date: "Enter the publication date in YYYY-MM-DD format"
language: "Enter the book's language code (e.g., en, de, fr)"
description: "Provide a detailed description of your book"
keywords:
  - "AI"
  - "machine learning"
  - "automation"
```

### 5️⃣ Convert the Book to PDF/EPUB/MOBI
Once the manuscript is ready, use the conversion script:
```bash
bash scripts/convert_book.sh
```
This will generate output files in the `output/` directory.

### 6️⃣ Start Writing

- Navigate to `manuscript/chapters/` and start writing your chapters in Markdown.
- Update `manuscript/front-matter/toc.md` to reflect your chapters and content.
- Store your images and figures in the `assets/` folder.

### 7️⃣ Convert to PDF, EPUB, and MOBI

Generate multiple book formats with the provided script:

```bash
chmod +x scripts/convert_book.sh
./scripts/convert_book.sh
```

Converted files will be available in the `output/` directory.

### 8️⃣ Push to GitHub

Commit and push your changes manually to GitHub:

```bash
git add .
git commit -m "Add new content or update chapters"
git push
```

---

## 📖 Documentation

Detailed guides and documentation to support your book writing process:

- [How to Write a Book: Step-by-Step Guide](how-to-write.md)
- [Full Export Documentation](full-export-documentation.md)
- [Create Project Structure Documentation](create-project-documentation.md)

---

Detailed documentation for exporting your book is available here:

- [Full Export Documentation](full-export-documentation.md)

---

## 📁 Directory Structure

```
write-book-template/
├── manuscript/
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
├── assets/               # Images and figures
├── config/               # Book configurations (metadata, styles)
├── output/               # Generated book formats
└── scripts/              # Automation scripts
    └── convert_book.sh   # 
    └── create_project_structure.sh  # 
    └── full-export-book.py  # 
├── README.md
├── LICENSE
```

---

## 🎨 Customization

- **Metadata:** Modify `config/metadata.yaml` to personalize your book details (title, author, etc.)
- **Styles:** Edit `config/styles.css` to tailor your book’s appearance and formatting.
- **Scripts:** Customize `convert_book.sh` to adjust conversion settings and output options.

---

## 🛠 Requirements

- [Pandoc](https://pandoc.org/installing.html) for manuscript conversion.
- [Calibre](https://calibre-ebook.com/download) specifically for MOBI conversions.
- [GitHub CLI (`gh`)](https://cli.github.com/) for managing repositories (optional but recommended).
- Python 3.x (for advanced automation with `full-export-book.py`)

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
