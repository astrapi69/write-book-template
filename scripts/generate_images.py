import os
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Load environment variables
load_dotenv()

def generate_image(prompt, filename, output_dir, api_key, style=None):
    full_prompt = f"{prompt}, in {style}" if style else prompt
    print(f"Generating: {filename}")

    response = requests.post(
        "https://api.deepai.org/api/text2img",
        data={'text': full_prompt},
        headers={'api-key': api_key}
    )

    if response.status_code != 200:
        print(f"❌ DeepAI error {response.status_code}: {response.text}")
        return

    try:
        image_url = response.json()['output_url']
        img_data = requests.get(image_url).content
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(img_data)
        print(f"✅ Saved: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save image for prompt: {full_prompt}\n{e}")

def main():
    parser = argparse.ArgumentParser(description="Generate images from prompts using DeepAI text2img")
    parser.add_argument("--prompt-file", required=True, help="Path to the prompt JSON file")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated images")
    parser.add_argument("--api-key", required=False, help="DeepAI API key (optional, overrides .env)")

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

    prompts = data.get("prompts", [])
    style = data.get("settings", {}).get("style", None)

    for item in prompts:
        generate_image(
            prompt=item.get("text", ""),
            filename=item.get("filename", "output.png"),
            output_dir=output_dir,
            api_key=api_key,
            style=style
        )

if __name__ == "__main__":
    main()
