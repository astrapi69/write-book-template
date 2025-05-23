#!/bin/bash
# !!! Note: this script is obsolete and will be removed in the next minor version. !!!
# !!! Use instead the full_export_book.py script. !!!
# Move to project root directory
cd "$(dirname "$0")/.."

# Define variables
BOOK_NAME="book"  # TODO change to your specific book name and delete this comment
INPUT_DIR="manuscript"
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

# Merge all markdown files in proper order
cat \
    "$INPUT_DIR/front-matter/book-title.md" \
    "$INPUT_DIR/front-matter/toc.md" \
    "$INPUT_DIR/front-matter/foreword.md" \
    "$INPUT_DIR/front-matter/preface.md" \
    "$INPUT_DIR/front-matter/acknowledgments.md" \
    "$INPUT_DIR/chapters/"*.md \
    "$INPUT_DIR/back-matter/epilogue.md" \
    "$INPUT_DIR/back-matter/glossary.md" \
    "$INPUT_DIR/back-matter/about-the-author.md" \
    "$INPUT_DIR/back-matter/acknowledgments.md" \
    "$INPUT_DIR/back-matter/appendix.md" \
    "$INPUT_DIR/back-matter/faq.md" \
    "$INPUT_DIR/back-matter/bibliography.md" \
    "$INPUT_DIR/back-matter/index.md" \
    > "$OUTPUT_DIR/$BOOK_NAME.md"

# Ensure Pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc is not installed. Install it using: sudo apt install pandoc"
    exit 1
fi
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
