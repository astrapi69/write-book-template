#!/bin/bash

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
    "$PROJECT_NAME/tools"
)

# Create directories
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
done

# Create sample files
touch "$PROJECT_NAME/manuscript/chapters/01-introduction.md"
touch "$PROJECT_NAME/manuscript/chapters/02-chapter-title.md"
touch "$PROJECT_NAME/manuscript/front-matter/toc.md"
touch "$PROJECT_NAME/manuscript/front-matter/preface.md"
touch "$PROJECT_NAME/manuscript/front-matter/acknowledgments.md"
touch "$PROJECT_NAME/manuscript/front-matter/foreword.md"
touch "$PROJECT_NAME/manuscript/back-matter/appendix.md"
touch "$PROJECT_NAME/manuscript/back-matter/glossary.md"
touch "$PROJECT_NAME/manuscript/back-matter/faq.md"
touch "$PROJECT_NAME/manuscript/back-matter/bibliography.md"
touch "$PROJECT_NAME/manuscript/back-matter/index.md"
touch "$PROJECT_NAME/manuscript/back-matter/about-the-author.md"
touch "$PROJECT_NAME/manuscript/references.bib"
touch "$PROJECT_NAME/config/metadata.yaml"
touch "$PROJECT_NAME/config/styles.css"
touch "$PROJECT_NAME/README.md"
touch "$PROJECT_NAME/LICENSE"

# Add basic content to README
echo "# Book Project" > "$PROJECT_NAME/README.md"
echo "This is the book project structure." >> "$PROJECT_NAME/README.md"

echo "✅ Book project structure created successfully!"
