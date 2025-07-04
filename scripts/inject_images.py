import json
import os
import re
import argparse
from pathlib import Path

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

CHAPTER_DIR = Path("manuscript/chapters")
IMAGE_DIR = Path("assets")
PROMPT_FILE = Path("assets/prompts/shadows_new_eden.json")

def load_prompts():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, dict) or "prompts" not in data:
            raise ValueError("Prompt JSON must contain a 'prompts' key with a list of prompt objects.")
        return data["prompts"]

def build_filename_map(prompts):
    # Maps chapter_01 → image filename
    return {
        Path(p["filename"]).stem[:10].lower(): p["filename"]
        for p in prompts
    }

def inject_image(content, image_filename):
    if f"![image]({image_filename})" in content:
        return content, False  # Already injected

    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("# chapter"):
            lines.insert(i + 1, f"\n![image]({IMAGE_DIR / image_filename})\n")
            return "\n".join(lines), True

    return content, False  # No header found

def main():
    parser = argparse.ArgumentParser(description="Inject generated images into chapter markdown files")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing changes to files")
    args = parser.parse_args()
    dry_run = args.dry_run

    prompts = load_prompts()
    filename_map = build_filename_map(prompts)
    chapter_files = sorted(CHAPTER_DIR.glob("*.md"))

    stats = {
        "total": 0,
        "injected": 0,
        "skipped_existing": 0,
        "missing_prompt": 0,
        "missing_image": 0,
    }

    for chapter_file in chapter_files:
        stats["total"] += 1

        # Normalize: e.g., 01-chapter.md → chapter_01
        number_part = chapter_file.stem.split("-")[0].zfill(2)
        chapter_key = f"chapter_{number_part}"

        image_file = filename_map.get(chapter_key)
        if not image_file:
            print(f"⚠️ No image defined for: {chapter_file.name} (key: {chapter_key})")
            stats["missing_prompt"] += 1
            continue

        full_image_path = IMAGE_DIR / image_file
        if not full_image_path.exists():
            print(f"⚠️ Image not found: {full_image_path}")
            stats["missing_image"] += 1
            continue

        content = chapter_file.read_text(encoding="utf-8")
        new_content, injected = inject_image(content, image_file)

        if not injected:
            print(f"ℹ️ Already contains image: {chapter_file.name}")
            stats["skipped_existing"] += 1
            continue

        if dry_run:
            print(f"🔍 Dry-run: would inject image into {chapter_file.name}")
        else:
            chapter_file.write_text(new_content, encoding="utf-8")
            print(f"✅ Image injected into: {chapter_file.name}")

        stats["injected"] += 1

    # Final summary
    print("\n📊 Summary")
    print("----------")
    print(f"📄 Total chapters processed: {stats['total']}")
    print(f"✅ Images injected:          {stats['injected']}")
    print(f"ℹ️ Already had image:       {stats['skipped_existing']}")
    print(f"❌ No prompt match:         {stats['missing_prompt']}")
    print(f"❌ Missing image file:      {stats['missing_image']}")

if __name__ == "__main__":
    main()
