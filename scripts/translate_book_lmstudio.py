"""
translate_book_lmstudio.py

Translate Markdown files using a local LM Studio REST API.
Supports recursive folder translation and intelligent fallback to chunked processing
for large files to avoid exceeding context limits.
"""

import os
import requests
import argparse

# Change working directory to project root (important if script is run from scripts/)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# Default LM Studio REST API endpoint
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"


def translate_text(text: str, source_lang: str = "en", target_lang: str = "es", model: str = "llama3") -> str:
    """
    Sends a translation request to LM Studio's REST API.

    Parameters:
        text (str): The text to be translated
        source_lang (str): Source language code (e.g., 'en')
        target_lang (str): Target language code (e.g., 'es')
        model (str): The name of the model loaded in LM Studio

    Returns:
        str: The translated text
    """
    system_prompt = f"Translate the following text from {source_lang.upper()} to {target_lang.upper()}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7
    }
    response = requests.post(LM_STUDIO_API_URL, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def translate_markdown_files(base_dir: str, source_lang: str = "en", target_lang: str = "es", model: str = "llama3"):
    """
    Recursively translates all Markdown (.md) files in a directory.

    Parameters:
        base_dir (str): Base directory to search for Markdown files
        source_lang (str): Source language code
        target_lang (str): Target language code
        model (str): Model name to use for translation
    """
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                translate_markdown_file(file_path, source_lang, target_lang, model)


def translate_markdown_file(file_path: str, source_lang: str = "en", target_lang: str = "es", model: str = "llama3"):
    """
    Translates a single Markdown file in-place. Falls back to paragraph-based
    chunked translation to avoid exceeding model context limits.

    Parameters:
        file_path (str): Path to the Markdown file
        source_lang (str): Source language code
        target_lang (str): Target language code
        model (str): Model name to use
    """
    print(f"Translating: {file_path} [{source_lang} → {target_lang}]")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return

    blocks = original_text.split("\n\n")  # Split by paragraph
    translated_blocks = []

    for block in blocks:
        if block.strip():
            try:
                translated = translate_text(block.strip(), source_lang, target_lang, model)
            except Exception as e:
                print(f"⚠️ Failed to translate block (keeping original):\n{block[:100]}...\nError: {e}")
                translated = block  # fallback: keep original
            translated_blocks.append(translated)
        else:
            translated_blocks.append("")

    translated_text = "\n\n".join(translated_blocks)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(translated_text)

    print(f"✅ Finished: {file_path}")


def main():
    """
    CLI entry point for translating all Markdown files in a directory.
    """
    parser = argparse.ArgumentParser(description="Translate markdown files using LM Studio REST API.")
    parser.add_argument("--source-lang", type=str, default="en", help="Source language code (default: en)")
    parser.add_argument("--target-lang", type=str, required=True, help="Target language code (e.g., es, fr)")
    parser.add_argument("--base-dir", type=str, default="manuscript", help="Directory containing Markdown files")

    args = parser.parse_args()
    translate_markdown_files(args.base_dir, args.source_lang, args.target_lang)

    # file_path = "manuscript/front-matter/toc.md"  # Relative to the project root
    #
    # print(f"🔍 Looking for: {os.path.abspath(file_path)}")
    #
    # file_path = os.path.abspath(file_path)
    # translate_markdown_file(
    #     file_path=file_path,
    #     source_lang="en",
    #     target_lang="fr",
    #     model="deepseek-r1-distill-qwen-7b"
    # )


if __name__ == "__main__":
    main()
