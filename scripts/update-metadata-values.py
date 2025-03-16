import re

# Define the replacement dictionary with descriptions
metadata_values = {
    "BOOK_TITLE": "Enter the title of your book",
    "BOOK_SUBTITLE": "Enter a short subtitle describing your book",
    "AUTHOR_NAME": "Enter the author's full name",
    "ISBN_NUMBER": "Enter the ISBN number (if available)",
    "BOOK_EDITION": "Enter the edition of the book (e.g., 1st Edition, 2nd Edition)",
    "PUBLISHER_NAME": "Enter the publisher's name",
    "PUBLICATION_DATE": "Enter the publication date in YYYY-MM-DD format",
    "LANGUAGE": "Enter the book's language code (e.g., en, de, fr)",
    "BOOK_DESCRIPTION": "Provide a detailed description of your book",
    "KEYWORDS": "Enter keywords separated by commas (e.g., AI, machine learning, automation)"
}

# Read metadata.yaml file
with open("config/metadata.yaml", "r") as file:
    content = file.read()

# Replace placeholders with actual descriptions
for key, value in metadata_values.items():
    content = re.sub(r"\{\{" + key + r"\}\}", value, content)

# Special handling for keywords array
content = re.sub(
    r"keywords:\s+- \{\{KEYWORDS\}\}",
    "keywords:\n  - " + "\n  - ".join(metadata_values["KEYWORDS"].split(", ")),
    content
)

# Write back to the file
with open("config/metadata.yaml", "w") as file:
    file.write(content)

print("✅ metadata.yaml now contains descriptions. Replace them with actual values before publishing!")
