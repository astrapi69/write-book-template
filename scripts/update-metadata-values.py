import json
import re
import os

# Define the path to the metadata values file
metadata_file = "config/metadata_values.json"

# Load metadata values from the JSON file if it exists
if os.path.exists(metadata_file):
    with open(metadata_file, "r", encoding="utf-8") as file:
        metadata_values = json.load(file)
else:
    metadata_values = {}

# Read metadata.yaml file
with open("config/metadata.yaml", "r", encoding="utf-8") as file:
    content = file.read()

# Replace placeholders with values from metadata_values.json
for key, value in metadata_values.items():
    if isinstance(value, list):
        # Format lists correctly for YAML (like keywords and output_formats)
        formatted_list = "\n  - " + "\n  - ".join(value)
        content = re.sub(r"\{\{" + key + r"\}\}", formatted_list, content)
    elif isinstance(value, bool):
        # Convert boolean values to lowercase (true/false)
        content = re.sub(r"\{\{" + key + r"\}\}", str(value).lower(), content)
    else:
        content = re.sub(r"\{\{" + key + r"\}\}", value, content)

# Write back to the file
with open("config/metadata.yaml", "w", encoding="utf-8") as file:
    file.write(content)

print("✅ metadata.yaml has been updated with values from metadata_values.json.")
