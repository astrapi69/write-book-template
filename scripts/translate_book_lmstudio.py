"""
translate_book_lmstudio.py

Translate Markdown files using a local LM Studio REST API (OpenAI-compatible).
- Recursively translates .md files
- Splits into paragraph-like blocks to avoid context limits
- Forces "translation only" output and strips <think> reasoning blocks
"""

from __future__ import annotations

import argparse
import os
import re
from typing import Optional

import requests

# Optional (fragile) behavior from your original script:
# If you run via poetry entrypoint, this isn't needed, but kept for compatibility.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

DEFAULT_API_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODELS_URL = "http://localhost:1234/v1/models"

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL | re.IGNORECASE)


def _strip_reasoning(text: str) -> str:
    """Remove common reasoning blocks and return only the visible answer."""
    if not text:
        return text

    cleaned = _THINK_BLOCK_RE.sub("", text).strip()

    # If model prints reasoning then final translation, last block is usually the answer
    parts = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if len(parts) >= 2:
        cleaned = parts[-1]

    # Remove accidental leading labels
    cleaned = re.sub(
        r"^(final|answer|übersetzung|translation)\s*:\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned


def _get_default_model_id(models_url: str, timeout_s: int = 10) -> str:
    """
    Fetch first available model id from LM Studio (/v1/models).
    Expected: {"data":[{"id":"..."}]}
    """
    r = requests.get(models_url, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    models = data.get("data") or []
    if not models or "id" not in models[0]:
        raise RuntimeError(
            f"Could not determine model id from {models_url}. Response: {str(data)[:800]}"
        )
    return models[0]["id"]


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    api_url: str,
    models_url: str,
    model: Optional[str] = None,
    temperature: float = 0.2,
    timeout_s: int = 120,
) -> str:
    """Translate text via LM Studio OpenAI-compatible endpoint; return translation only."""
    if not model:
        model = _get_default_model_id(models_url)

    system_prompt = (
        "You are a professional translation engine.\n"
        f"Translate the text from {source_lang.upper()} to {target_lang.upper()}.\n"
        "Output ONLY the translated text.\n"
        "Do NOT explain your reasoning.\n"
        "Do NOT add comments.\n"
        "Do NOT include tags like <think> or </think>.\n"
        "Do NOT repeat the original text.\n"
        "Preserve Markdown formatting exactly (headings, lists, emphasis, links, code blocks).\n"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": temperature,
    }

    r = requests.post(api_url, json=payload, timeout=timeout_s)

    if r.status_code == 400:
        raise RuntimeError(f"LM Studio returned 400 Bad Request. Body: {r.text[:1200]}")
    if r.status_code == 404:
        raise RuntimeError(
            f"LM Studio returned 404 Not Found. Check api_url={api_url} and server mode. Body: {r.text[:800]}"
        )
    r.raise_for_status()

    data = r.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(f"Unexpected response from LM Studio: {str(data)[:1200]}")

    return _strip_reasoning(content)


def translate_markdown_file(
    file_path: str,
    source_lang: str,
    target_lang: str,
    api_url: str,
    models_url: str,
    model: Optional[str] = None,
    skip_html_tr_rows: bool = True,
):
    """
    Translates a single Markdown file **in place** using a local or remote LLM API.

    The file is split into paragraph-sized blocks (separated by blank lines)
    to reduce the risk of exceeding model context limits. Each block is translated
    independently. Empty blocks are preserved.

    HTML table rows (<tr>...</tr>) can be optionally excluded from translation
    to avoid breaking table structures.

    On translation errors, the original block is kept and processing continues.

    Parameters:
        file_path (str): Path to the Markdown file to translate (will be overwritten)
        source_lang (str): Source language code (e.g. "en")
        target_lang (str): Target language code (e.g. "de")
        api_url (str): Base URL of the translation / chat completion API
        models_url (str): URL endpoint used to resolve available models
        model (Optional[str]): Explicit model name to use (auto-selected if None)
        skip_html_tr_rows (bool): If True, blocks starting with "<tr>" are copied verbatim
    """
    print(f"Translating: {file_path} [{source_lang} → {target_lang}]")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return

    blocks = original_text.split("\n\n")
    translated_blocks: list[str] = []

    for block in blocks:
        if not block.strip():
            translated_blocks.append("")
            continue

        if skip_html_tr_rows and block.lstrip().startswith("<tr>"):
            translated_blocks.append(block)
            continue

        try:
            translated = translate_text(
                block.strip(),
                source_lang=source_lang,
                target_lang=target_lang,
                api_url=api_url,
                models_url=models_url,
                model=model,
            )
        except Exception as e:
            print(
                f"⚠️ Failed to translate block (keeping original):\n{block[:120]}...\nError: {e}"
            )
            translated = block

        translated_blocks.append(translated)

    translated_text = "\n\n".join(translated_blocks)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(translated_text)

    print(f"✅ Finished: {file_path}")


def translate_markdown_files(
    base_dir: str,
    source_lang: str,
    target_lang: str,
    api_url: str,
    models_url: str,
    model: Optional[str] = None,
    skip_html_tr_rows: bool = True,
):
    """
    Recursively translates all Markdown (.md) files within a directory tree.

    Walks the given base directory and processes every Markdown file found
    by delegating to `translate_markdown_file()`. Files are translated
    **in place**; existing content will be overwritten.

    Subdirectories are traversed depth-first via `os.walk`.

    Parameters:
        base_dir (str): Root directory containing Markdown files
        source_lang (str): Source language code (e.g. "en")
        target_lang (str): Target language code (e.g. "fr")
        api_url (str): Base URL of the translation / chat completion API
        models_url (str): URL endpoint used to resolve available models
        model (Optional[str]): Explicit model name to use (auto-selected if None)
        skip_html_tr_rows (bool): If True, blocks starting with "<tr>" are copied verbatim
    """
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                translate_markdown_file(
                    file_path=file_path,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    api_url=api_url,
                    models_url=models_url,
                    model=model,
                    skip_html_tr_rows=skip_html_tr_rows,
                )


def main():
    parser = argparse.ArgumentParser(
        description="Translate markdown files using LM Studio REST API (OpenAI-compatible)."
    )
    parser.add_argument("--source-lang", type=str, default="en")
    parser.add_argument("--target-lang", type=str, required=True)
    parser.add_argument("--base-dir", type=str, default="manuscript")
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("LM_STUDIO_API_URL", DEFAULT_API_URL),
        help=f"Chat completions endpoint (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--models-url",
        type=str,
        default=os.getenv("LM_STUDIO_MODELS_URL", DEFAULT_MODELS_URL),
        help=f"Models endpoint (default: {DEFAULT_MODELS_URL})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LM_STUDIO_MODEL", None),
        help="Optional explicit model id. If omitted, first id from /v1/models is used.",
    )
    parser.add_argument(
        "--no-skip-html-tr",
        action="store_true",
        help="Do not skip translating HTML <tr> rows (default skips them).",
    )

    args = parser.parse_args()

    translate_markdown_files(
        base_dir=args.base_dir,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        api_url=args.api_url,
        models_url=args.models_url,
        model=args.model,
        skip_html_tr_rows=(not args.no_skip_html_tr),
    )


if __name__ == "__main__":
    main()
