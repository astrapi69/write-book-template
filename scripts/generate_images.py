# scripts/generate_images.py
import os
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Set working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Load environment variables from .env
load_dotenv()


def load_character_profiles(path="scripts/data/character_profiles.json"):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load character profiles: {e}")
        return {}


def generate_image(prompt, filename, output_dir, api_key):
    output_path = Path(output_dir) / filename
    if output_path.exists():
        print(f"⚠️ Skipped: {filename} already exists")
        return

    print(f"🎨 Generating: {filename}")

    response = requests.post(
        "https://api.deepai.org/api/text2img",
        data={"text": prompt},
        headers={"api-key": api_key},
    )

    if response.status_code != 200:
        print(f"❌ DeepAI error {response.status_code}: {response.text}")
        return

    try:
        image_url = response.json()["output_url"]
        img_data = requests.get(image_url).content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_data)
        print(f"✅ Saved: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save image for prompt: {prompt}\n{e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images from prompts using DeepAI text2img"
    )
    parser.add_argument(
        "--prompt-file",
        default="scripts/data/image_prompts.json",
        help="Path to the prompt JSON file (default: scripts/data/image_prompts.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/illustrations"),
        help="Directory to save generated images (default: assets/illustrations)",
    )
    parser.add_argument(
        "--api-key", required=False, help="DeepAI API key (optional, overrides .env)"
    )
    parser.add_argument(
        "--character-profile",
        default="scripts/data/character_profiles.json",
        help="Path to character profile JSON file",
    )
    args = parser.parse_args()

    prompt_file = Path(args.prompt_file)
    output_dir = Path(args.output_dir)
    api_key = args.api_key or os.getenv("DEEPAI_API_KEY")

    if not api_key:
        print("❌ No API key provided. Set --api-key or define DEEPAI_API_KEY in .env")
        return

    if not prompt_file.exists():
        print(f"❌ Prompt file does not exist: {prompt_file}")
        return

    with open(prompt_file, encoding="utf-8") as f:
        data = json.load(f)

    global_style = data.get("style", None)
    character_profiles = load_character_profiles(args.character_profile)

    chapters = data.get("chapters", [])
    for chapter in chapters:
        prompts = chapter.get("prompts", [])
        for item in prompts:
            base_prompt = item.get("prompt", "")
            character_key = item.get("character", None)

            # Unterstützt Liste oder Einzelwert
            if isinstance(character_key, list):
                character_desc = ", ".join(
                    [character_profiles.get(name, "") for name in character_key]
                )
            else:
                character_desc = character_profiles.get(character_key, "")

            combined = (
                f"{character_desc}, {base_prompt}" if character_desc else base_prompt
            )
            final_prompt = f"{combined}, {global_style}" if global_style else combined

            filename = item.get("filename", "output.png")
            generate_image(
                prompt=final_prompt,
                filename=filename,
                output_dir=output_dir,
                api_key=api_key,
            )


if __name__ == "__main__":
    main()
