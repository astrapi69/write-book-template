#!/bin/bash

# Move to project root directory
cd "$(dirname "$0")/.."

# Set project name
PROJECT_NAME="."

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
)

# Create directories
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
done

# Create sample files
touch "$PROJECT_NAME/manuscript/chapters/01-chapter.md"
touch "$PROJECT_NAME/manuscript/chapters/02-chapter.md"
touch "$PROJECT_NAME/manuscript/front-matter/book-title.md"
touch "$PROJECT_NAME/manuscript/front-matter/foreword.md"
touch "$PROJECT_NAME/manuscript/front-matter/preface.md"
touch "$PROJECT_NAME/manuscript/front-matter/toc.md"
touch "$PROJECT_NAME/manuscript/back-matter/about-the-author.md"
touch "$PROJECT_NAME/manuscript/back-matter/acknowledgments.md"
touch "$PROJECT_NAME/manuscript/back-matter/appendix.md"
touch "$PROJECT_NAME/manuscript/back-matter/bibliography.md"
touch "$PROJECT_NAME/manuscript/back-matter/epilogue.md"
touch "$PROJECT_NAME/manuscript/back-matter/faq.md"
touch "$PROJECT_NAME/manuscript/back-matter/glossary.md"
touch "$PROJECT_NAME/manuscript/back-matter/index.md"
touch "$PROJECT_NAME/manuscript/references.bib"
touch "$PROJECT_NAME/config/amazon-kdp-info.md"
touch "$PROJECT_NAME/config/book-description.html"
touch "$PROJECT_NAME/config/cover-back-page-author-introduction.md"
touch "$PROJECT_NAME/config/cover-back-page-description.md"
touch "$PROJECT_NAME/config/keywords.md"
touch "$PROJECT_NAME/config/styles.css"
touch "$PROJECT_NAME/README.md"
touch "$PROJECT_NAME/LICENSE"

# Add basic content to README
echo "# Book Project" > "$PROJECT_NAME/README.md"
echo "This is the book project structure." >> "$PROJECT_NAME/README.md"

# Fill metadata.yaml with AI-friendly placeholders
cat > "$PROJECT_NAME/config/metadata.yaml" <<EOL
title: "{{BOOK_TITLE}}"
subtitle: "{{BOOK_SUBTITLE}}"
author: "{{AUTHOR_NAME}}"
isbn: "{{ISBN_NUMBER}}"
edition: "{{BOOK_EDITION}}"
publisher: "{{PUBLISHER_NAME}}"
date: "{{PUBLICATION_DATE}}"
language: "{{LANGUAGE}}"
description: "{{BOOK_DESCRIPTION}}"
keywords: {{KEYWORDS}}
cover_image: "{{COVER_IMAGE}}"
output_formats: {{OUTPUT_FORMATS}}
kdp_enabled: {{KDP_ENABLED}}
EOL

# Create default metadata_values.json with empty placeholders
cat > "$PROJECT_NAME/config/metadata_values.json" <<EOL
{
  "BOOK_TITLE": "",
  "BOOK_SUBTITLE": "",
  "AUTHOR_NAME": "",
  "ISBN_NUMBER": "",
  "BOOK_EDITION": "",
  "PUBLISHER_NAME": "",
  "PUBLICATION_DATE": "",
  "LANGUAGE": "",
  "BOOK_DESCRIPTION": "",
  "KEYWORDS": [],
  "COVER_IMAGE": "",
  "OUTPUT_FORMATS": ["pdf", "epub", "mobi", "docx"],
  "KDP_ENABLED": false
}
EOL

echo "✅ Book project structure created successfully!"
echo "ℹ️  You can edit config/metadata_values.json and run the metadata script(scripts/update_metadata_values.py) to populate metadata.yaml automatically."
