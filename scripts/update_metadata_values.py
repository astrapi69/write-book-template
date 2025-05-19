import json
import re
import os

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")


def main():
    metadata_file = "config/metadata_values.json"
    yaml_file = "config/metadata.yaml"

    default_metadata = {
        "BOOK_TITLE": "Enter the title of your book",
        "BOOK_SUBTITLE": "Enter a short subtitle describing your book",
        "AUTHOR_NAME": "Enter the author's full name",
        "ISBN_NUMBER": "Enter the ISBN number (if available)",
        "BOOK_EDITION": "Enter the edition of the book (e.g., 1st Edition, 2nd Edition)",
        "PUBLISHER_NAME": "Enter the publisher's name",
        "PUBLICATION_DATE": "Enter the publication date in YYYY-MM-DD format",
        "LANGUAGE": "Enter the book's language code (e.g., en, de, fr)",
        "BOOK_DESCRIPTION": "Provide a detailed description of your book",
        "KEYWORDS": ["Enter some keywords here"],
        "COVER_IMAGE": "",
        "OUTPUT_FORMATS": ["pdf", "epub", "mobi", "docx"],
        "KDP_ENABLED": False
    }

    try:
        # Load metadata from JSON if it exists, otherwise use defaults
        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as file:
                metadata_values = json.load(file)
        else:
            metadata_values = default_metadata

        # Normalize KEYWORDS if it's a string
        if isinstance(metadata_values.get("KEYWORDS"), str):
            metadata_values["KEYWORDS"] = [k.strip() for k in metadata_values["KEYWORDS"].split(",")]

        # Read metadata.yaml
        with open(yaml_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Replace placeholders
        for key, value in metadata_values.items():
            if isinstance(value, list):
                formatted_list = "\n  - " + "\n  - ".join(value)
                content = re.sub(r"\{\{" + key + r"\}\}", formatted_list, content)
            elif isinstance(value, bool):
                content = re.sub(r"\{\{" + key + r"\}\}", str(value).lower(), content)
            else:
                content = re.sub(r"\{\{" + key + r"\}\}", str(value), content)

        # Write the updated YAML
        with open(yaml_file, "w", encoding="utf-8") as file:
            file.write(content)

        print("✅ metadata.yaml has been updated with values from metadata_values.json.")

        # Delete the JSON file after successful transfer
        if os.path.exists(metadata_file):
            os.remove(metadata_file)
            print("🗑️ metadata_values.json has been deleted.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
