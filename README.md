
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

### 2️⃣ Set Up Your Book Repository

Run the setup script to initialize your new book project:

```bash
chmod +x create_project_structure.sh
./create_project_structure.sh
```

This generates all necessary folders and files.

### 3️⃣ Start Writing

- Navigate to `manuscript/chapters/` and start writing your chapters in Markdown.
- Update `manuscript/front-matter/toc.md` to reflect your chapters and content.
- Store your images and figures in the `assets/` folder.

### 4️⃣ Convert to PDF, EPUB, and MOBI

Generate multiple book formats with the provided script:

```bash
chmod +x convert_book.sh
./convert_book.sh
```

Converted files will be available in the `output/` directory.

### 5️⃣ Push to GitHub

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

---

## 🤝 Contributing

Contributions are warmly welcomed! Feel free to submit issues, suggestions, or pull requests to help improve this template.

---

## 📄 License

Released under the MIT License. Please see the `LICENSE` file for details.

---

🚀 **Happy writing! Start your book today!**
