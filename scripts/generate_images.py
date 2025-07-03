# generate_images.py
import os
import json
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
API_KEY = os.getenv("DEEPAI_API_KEY")

DEEPAI_API_KEY = API_KEY
OUTPUT_DIR = Path("assets")
PROMPT_FILE = Path("assets/prompts/die_jaeger_und_die_gejagten.json")

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

def generate_image(prompt, filename, style=None):
    # Merge style into prompt text
    if style:
        full_prompt = f"{prompt}, in {style}"
    else:
        full_prompt = prompt

    print(f"Generating: {filename}")
    response = requests.post(
        "https://api.deepai.org/api/text2img",
        data={'text': full_prompt},
        headers={'api-key': API_KEY}
    )

    if response.status_code != 200:
        print(f"❌ DeepAI error {response.status_code}: {response.text}")
        return

    try:
        image_url = response.json()['output_url']
        img_data = requests.get(image_url).content
        with open(OUTPUT_DIR / filename, 'wb') as f:
            f.write(img_data)
        print(f"✅ Saved: {filename}")
    except Exception as e:
        print(f"❌ Failed to save image for prompt: {full_prompt}\n{e}")

def main():
    with open(PROMPT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    prompts = data.get("prompts", [])
    style = data.get("settings", {}).get("style", None)

    for item in prompts:
        generate_image(
            prompt=item.get("text", ""),
            filename=item.get("filename", "output.png"),
            style=style
        )

if __name__ == "__main__":
    main()
