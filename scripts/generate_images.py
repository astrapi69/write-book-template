import os
import json
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Set working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Load environment variables
load_dotenv()
API_KEY = os.getenv("DEEPAI_API_KEY")
DEEPAI_URL = "https://api.deepai.org/api/text2img"

# Paths
OUTPUT_DIR = Path("assets")
PROMPT_FILE = Path("assets/prompts/image_prompts.json")

def generate_image(prompt, filename, style=None, dry_run=False):
    full_prompt = f"{prompt}, in {style}" if style else prompt
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"⏭️  Skipping (already exists): {filename}")
        return "skipped"

    if dry_run:
        print(f"🔍 Dry-run: would generate '{filename}' with prompt: {full_prompt}")
        return "dry-run"

    print(f"⚙️ Generating: {filename}")
    try:
        response = requests.post(
            DEEPAI_URL,
            data={"text": full_prompt},
            headers={"api-key": API_KEY}
        )

        if response.status_code != 200:
            print(f"❌ DeepAI error {response.status_code}: {response.text}")
            return "error"

        image_url = response.json()["output_url"]
        img_data = requests.get(image_url).content

        with open(output_path, "wb") as f:
            f.write(img_data)

        print(f"✅ Saved: {filename}")
        return "generated"
    except Exception as e:
        print(f"❌ Failed to generate '{filename}': {e}")
        return "error"

def main():
    parser = argparse.ArgumentParser(description="Generate images using DeepAI Text2Image API")
    parser.add_argument("--dry-run", action="store_true", help="Simulate image generation without API calls")
    args = parser.parse_args()

    with open(PROMPT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    prompts = data.get("prompts", [])
    style = data.get("settings", {}).get("style", None)

    stats = {"total": 0, "generated": 0, "skipped": 0, "errors": 0, "dry_run": 0}

    for item in prompts:
        stats["total"] += 1
        result = generate_image(
            prompt=item.get("text", ""),
            filename=item.get("filename", "output.png"),
            style=style,
            dry_run=args.dry_run
        )
        if result == "generated":
            stats["generated"] += 1
        elif result == "skipped":
            stats["skipped"] += 1
        elif result == "error":
            stats["errors"] += 1
        elif result == "dry-run":
            stats["dry_run"] += 1

    # Summary
    print("\n📊 Summary")
    print("----------")
    print(f"📄 Prompts processed:   {stats['total']}")
    print(f"✅ Images generated:    {stats['generated']}")
    print(f"⏭️  Skipped (existing):  {stats['skipped']}")
    print(f"🔍 Dry-run entries:     {stats['dry_run']}")
    print(f"❌ Errors:              {stats['errors']}")

if __name__ == "__main__":
    main()
