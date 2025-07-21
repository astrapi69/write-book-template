"""
translate_book_deepl.py

Translate Markdown files using the DeepL Free API.
Overwrites original files. Supports skiplist, dry-run mode, and logs skipped files.
"""

import os
import requests
import argparse
from time import sleep
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DEEPL_AUTH_KEY = os.getenv("DEEPL_AUTH_KEY")

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

# Constants
SKIPLIST_PATH = ".skiplist"
SKIPPED_LOG_PATH = "logs/skipped.log"
TRANSLATION_DELAY = 1  # seconds

# Ensure working from project root
script_path = os.path.realpath(__file__)
project_root = os.path.abspath(os.path.join(os.path.dirname(script_path), ".."))
os.chdir(project_root)

def normalize_path(path: str) -> str:
    """Normalize paths relative to project root to ensure consistent skiplist behavior"""
    return os.path.normpath(os.path.relpath(path, start=project_root))

def load_skiplist(path: str = SKIPLIST_PATH) -> set:
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(normalize_path(line.strip()) for line in f if line.strip())

def log_skipped(reason: str, file_path: str):
    os.makedirs(os.path.dirname(SKIPPED_LOG_PATH), exist_ok=True)
    with open(SKIPPED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{reason}: {file_path}\n")

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if not DEEPL_AUTH_KEY:
        raise EnvironmentError("❌ Please set the DEEPL_AUTH_KEY environment variable.")

    data = {
        "auth_key": DEEPL_AUTH_KEY,
        "text": text,
        "source_lang": source_lang.upper(),
        "target_lang": target_lang.upper()
    }

    response = requests.post(DEEPL_API_URL, data=data)
    response.raise_for_status()
    return response.json()["translations"][0]["text"]

def translate_markdown_files(base_dir: str, source_lang: str, target_lang: str, skiplist: set, translated_files: set, dry_run: bool):
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                translate_markdown_file(file_path, source_lang, target_lang, skiplist, translated_files, dry_run)

def translate_markdown_file(file_path: str, source_lang: str, target_lang: str, skiplist: set, translated_files: set, dry_run: bool):
    norm_path = normalize_path(file_path)

    if norm_path in skiplist:
        print(f"⏭️ Skipped via .skiplist: {norm_path}")
        log_skipped("skiplist", norm_path)
        return

    print(f"🌍 Translating: {norm_path} [{source_lang} → {target_lang}]")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {norm_path}")
        log_skipped("not_found", norm_path)
        return

    if not original_text.strip():
        print(f"⏭️ Skipped empty file: {norm_path}")
        translated_files.add(norm_path)
        log_skipped("empty", norm_path)
        return

    blocks = original_text.split("\n\n")
    translated_blocks = []

    for block in blocks:
        if block.strip():
            try:
                translated = translate_text(block.strip(), source_lang, target_lang) if not dry_run else block
                sleep(TRANSLATION_DELAY)
            except Exception as e:
                print(f"⚠️ Failed to translate block:\n{block[:100]}...\nError: {e}")
                translated = block
            translated_blocks.append(translated)
        else:
            translated_blocks.append("")

    translated_text = "\n\n".join(translated_blocks)

    if not dry_run:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(translated_text)
        print(f"✅ Overwritten: {norm_path}")
    else:
        print(f"🧪 Dry-run complete: {norm_path} not written.")

    translated_files.add(norm_path)
    print(f"📌 Added to translated_files: {norm_path}")

def main():
    parser = argparse.ArgumentParser(description="Translate markdown files using DeepL Free API.")
    parser.add_argument("--source-lang", type=str, default="EN", help="Source language code (default: EN)")
    parser.add_argument("--target-lang", type=str, required=True, help="Target language code (e.g., DE, FR)")
    parser.add_argument("--base-dir", type=str, help="Directory containing Markdown files")
    parser.add_argument("--file", type=str, help="Path to a specific Markdown file")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing files or updating skiplist")

    args = parser.parse_args()
    skiplist = load_skiplist()
    translated_files = set()

    try:
        if args.file:
            translate_markdown_file(args.file, args.source_lang, args.target_lang, skiplist, translated_files, args.dry_run)
        elif args.base_dir:
            translate_markdown_files(args.base_dir, args.source_lang, args.target_lang, skiplist, translated_files, args.dry_run)
        else:
            parser.error("You must specify either --file or --base-dir.")
    except KeyboardInterrupt:
        print("\n🛑 Translation interrupted by user (Ctrl+C)")
    finally:
        if not args.dry_run and translated_files:
            print(f"📊 Total files marked as translated: {len(translated_files)}")

            normalized_translated = {normalize_path(path) for path in translated_files}
            current_skiplist = load_skiplist()
            new_entries = sorted(normalized_translated - current_skiplist)
            combined_entries = sorted(current_skiplist.union(normalized_translated))

            if new_entries:
                os.makedirs(os.path.dirname(SKIPLIST_PATH) or ".", exist_ok=True)
                with open(SKIPLIST_PATH, "w", encoding="utf-8") as f:
                    for path in combined_entries:
                        print(f"📄 Writing to .skiplist: {path}")
                        f.write(path + "\n")
                print(f"📝 Skiplist updated with {len(new_entries)} new entries (total {len(combined_entries)}).")
            else:
                print("ℹ️ No new entries to add to skiplist.")


if __name__ == "__main__":
    main()
