#!/usr/bin/env python3
"""
📘 Script: translate_book_lmstudio.py

Translate Markdown files using a local (or intranet-hosted) LM Studio instance via its
OpenAI-compatible REST API.

This script works **in-place**: it overwrites the original Markdown files.

---

## ✅ Features

- Translate a **single file** (`--file`) or a **directory recursively** (`--base-dir`)
- Paragraph/block-based chunking (splits by blank lines)
- Preserves Markdown formatting (headings, lists, links, code blocks)
- Strips common reasoning outputs (e.g. `<think>...</think>`)
- Optional: skip translating HTML table rows starting with `<tr>` (default ON)
- **Remember/Skiplist feature**:
  - Skips files listed in `.skiplist`
  - Marks processed files and writes them into `.skiplist` at the end
- `--dry-run` mode:
  - No file writes
  - No skiplist updates
  - Still reports/logs what would happen
- Logs skipped files to `logs/skipped.log`

---

## 🔧 Requirements

- Python 3.10+
- `requests` installed
- LM Studio running with an OpenAI-compatible server enabled:
  - Chat Completions endpoint: `http://localhost:1234/v1/chat/completions`
  - Models endpoint: `http://localhost:1234/v1/models`

Install dependency:
    pip install requests

---

## 🚀 Usage

Translate recursively in default folder `manuscript` (EN -> ES):
    python scripts/translate_book_lmstudio.py --target-lang es

Translate a single file:
    python scripts/translate_book_lmstudio.py --target-lang fr --file manuscript/chapters/chapter-01.md

Translate a different base directory:
    python scripts/translate_book_lmstudio.py --target-lang de --base-dir manuscript/chapters

Dry-run (no writes, no skiplist update):
    python scripts/translate_book_lmstudio.py --target-lang it --dry-run

Disable skipping HTML <tr> rows:
    python scripts/translate_book_lmstudio.py --target-lang es --no-skip-html-tr

Use an intranet LM Studio host:
    python scripts/translate_book_lmstudio.py --target-lang es \
        --api-url http://lmstudio.intranet:1234/v1/chat/completions \
        --models-url http://lmstudio.intranet:1234/v1/models

Force a specific model id:
    python scripts/translate_book_lmstudio.py --target-lang es --model "llama-3.1-8b-instruct"

---

## Parameters

### Required
- `--target-lang <code>`
  - Target language code (e.g. `de`, `en`, `fr`, `es`).

### Optional
- `--source-lang <code>`
  - Source language code.
  - Default: `en`

- `--base-dir <path>`
  - Base directory to scan recursively for `*.md`.
  - Default: `manuscript`
  - Ignored if `--file` is set.

- `--file <path>`
  - Translate a single Markdown file (in place).
  - Overrides `--base-dir`.

- `--api-url <url>`
  - LM Studio chat completions endpoint.
  - Default: `http://localhost:1234/v1/chat/completions`
  - Env override: `LM_STUDIO_API_URL`

- `--models-url <url>`
  - LM Studio models endpoint (used to auto-detect a default model).
  - Default: `http://localhost:1234/v1/models`
  - Env override: `LM_STUDIO_MODELS_URL`

- `--model <model-id>`
  - Force a specific model id. If omitted, the script picks the first id from `/v1/models`.
  - Env override: `LM_STUDIO_MODEL`

- `--no-skip-html-tr`
  - By default, blocks that start with `<tr>` are not translated to avoid breaking HTML tables.
  - This flag disables that behavior.

- `--dry-run`
  - Run without writing files and without updating `.skiplist`.

---

## Remember / Skiplist (“Merkfeature”)

- `.skiplist` (project root)
  - Stores **normalized relative paths** (relative to project root).
  - Files in this list are skipped on future runs.

- `logs/skipped.log`
  - Records skip events with a reason:
    - `skiplist: <path>` (already in `.skiplist`)
    - `empty: <path>` (file is empty)
    - `not_found: <path>` (file not found)

Important:
- Without `--dry-run`, the script writes all processed file paths into `.skiplist` at the end.
- With `--dry-run`, nothing is written and `.skiplist` is not changed.

---

## Notes / Limitations

- This script uses a simple “split by blank line” chunking strategy. Very long paragraphs can still be large.
- If translation fails for a block, the original block is kept to prevent data loss.
"""

from __future__ import annotations

import argparse
import os
import re
from time import sleep
from typing import Optional

import requests

# Optional (fragile) behavior from your original script:
# If you run via poetry entrypoint, this isn't needed, but kept for compatibility.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

# ---- Defaults / Config ----
DEFAULT_API_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODELS_URL = "http://localhost:1234/v1/models"

SKIPLIST_PATH = ".skiplist"
SKIPPED_LOG_PATH = "logs/skipped.log"

# Throttle between blocks if needed (seconds). Keep 0 by default.
TRANSLATION_DELAY = 0

# Strip common reasoning blocks
_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL | re.IGNORECASE)

# Ensure we operate from project root
SCRIPT_PATH = os.path.realpath(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(SCRIPT_PATH), ".."))
os.chdir(PROJECT_ROOT)


# ---- Skiplist helpers ----
def normalize_path(path: str) -> str:
    """Normalize file paths to be stable across runs and machines (relative to project root)."""
    return os.path.normpath(os.path.relpath(path, start=PROJECT_ROOT))


def load_skiplist(path: str = SKIPLIST_PATH) -> set[str]:
    """Load skiplist file if present; returns normalized relative paths."""
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {normalize_path(line.strip()) for line in f if line.strip()}


def log_skipped(reason: str, file_path: str) -> None:
    """Append a skip event to logs/skipped.log."""
    os.makedirs(os.path.dirname(SKIPPED_LOG_PATH), exist_ok=True)
    with open(SKIPPED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{reason}: {file_path}\n")


# ---- LLM response cleanup ----
def strip_reasoning(text: str) -> str:
    """
    Remove common reasoning markup and keep only the final translated content.
    This is defensive: models may still output extra sections.
    """
    if not text:
        return text

    cleaned = _THINK_BLOCK_RE.sub("", text).strip()

    # If the model prints multiple "sections", last block is usually the actual translation.
    parts = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if len(parts) >= 2:
        cleaned = parts[-1]

    # Remove accidental leading labels
    cleaned = re.sub(
        r"^(final|answer|translation|übersetzung)\s*:\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    return cleaned


# ---- LM Studio / OpenAI-compatible API ----
def get_default_model_id(models_url: str, timeout_s: int = 10) -> str:
    """
    Fetch the first available model id from LM Studio /v1/models.

    Expected response:
      {"data":[{"id":"..."}]}
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
    """
    Translate a text block using LM Studio's OpenAI-compatible Chat Completions endpoint.
    Returns translated text only.
    """
    if not model:
        model = get_default_model_id(models_url)

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

    # Explicit diagnostics for common misconfigurations
    if r.status_code == 404:
        raise RuntimeError(
            f"LM Studio returned 404 Not Found. Check api_url={api_url}. Body: {r.text[:800]}"
        )
    if r.status_code == 400:
        raise RuntimeError(f"LM Studio returned 400 Bad Request. Body: {r.text[:1200]}")

    r.raise_for_status()
    data = r.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(f"Unexpected response from LM Studio: {str(data)[:1200]}")

    return strip_reasoning(content)


# ---- File translation ----
def translate_markdown_file(
    file_path: str,
    source_lang: str,
    target_lang: str,
    api_url: str,
    models_url: str,
    skiplist: set[str],
    translated_files: set[str],
    dry_run: bool,
    model: Optional[str] = None,
    skip_html_tr_rows: bool = True,
) -> None:
    """
    Translate one markdown file in place.

    Remember/Skiplist behavior:
    - If file is listed in `.skiplist`: skip and log
    - If file is empty: skip, log, and (optionally) mark as translated (so it will be remembered)
    - On success: add to `translated_files` for later `.skiplist` persistence
    - In dry-run: no writes and no `.skiplist` updates
    """
    norm_path = normalize_path(file_path)

    if norm_path in skiplist:
        print(f"⏭️  Skipped via .skiplist: {norm_path}")
        log_skipped("skiplist", norm_path)
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {norm_path}")
        log_skipped("not_found", norm_path)
        return

    if not original_text.strip():
        print(f"⏭️  Skipped empty file: {norm_path}")
        log_skipped("empty", norm_path)
        translated_files.add(norm_path)
        return

    print(f"🌍 Translating: {norm_path} [{source_lang} → {target_lang}]")

    # Block splitting by blank lines. This keeps Markdown intact in most cases.
    blocks = original_text.split("\n\n")
    translated_blocks: list[str] = []

    for block in blocks:
        if not block.strip():
            translated_blocks.append("")
            continue

        # Optional: skip HTML table row blocks to avoid breaking tables.
        if skip_html_tr_rows and block.lstrip().startswith("<tr>"):
            translated_blocks.append(block)
            continue

        if dry_run:
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
            if TRANSLATION_DELAY:
                sleep(TRANSLATION_DELAY)
        except Exception as e:
            print(
                f"⚠️  Failed to translate block (keeping original). "
                f"Error: {e}\nBlock preview: {block[:160]!r}"
            )
            translated = block

        translated_blocks.append(translated)

    translated_text = "\n\n".join(translated_blocks)

    if dry_run:
        print(f"🧪 Dry-run complete: {norm_path} not written.")
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(translated_text)
        print(f"✅ Overwritten: {norm_path}")

    translated_files.add(norm_path)


def translate_markdown_files(
    base_dir: str,
    source_lang: str,
    target_lang: str,
    api_url: str,
    models_url: str,
    skiplist: set[str],
    translated_files: set[str],
    dry_run: bool,
    model: Optional[str] = None,
    skip_html_tr_rows: bool = True,
) -> None:
    """Recursively translate all `*.md` files under `base_dir`."""
    for root, _, files in os.walk(base_dir):
        for filename in files:
            if not filename.endswith(".md"):
                continue
            file_path = os.path.join(root, filename)
            translate_markdown_file(
                file_path=file_path,
                source_lang=source_lang,
                target_lang=target_lang,
                api_url=api_url,
                models_url=models_url,
                skiplist=skiplist,
                translated_files=translated_files,
                dry_run=dry_run,
                model=model,
                skip_html_tr_rows=skip_html_tr_rows,
            )


def persist_skiplist(translated_files: set[str], dry_run: bool) -> None:
    """
    Merge translated_files into `.skiplist` (normalized relative paths), unless dry-run.
    """
    if dry_run:
        return

    if not translated_files:
        print("ℹ️  No files to add to skiplist.")
        return

    current = load_skiplist(SKIPLIST_PATH)
    normalized = {normalize_path(p) for p in translated_files}
    new_entries = sorted(normalized - current)
    combined = sorted(current.union(normalized))

    if not new_entries:
        print("ℹ️  No new entries to add to skiplist.")
        return

    # Ensure parent exists (project root typically)
    os.makedirs(os.path.dirname(SKIPLIST_PATH) or ".", exist_ok=True)

    with open(SKIPLIST_PATH, "w", encoding="utf-8") as f:
        for p in combined:
            f.write(p + "\n")

    print(
        f"📝 Skiplist updated with {len(new_entries)} new entries "
        f"(total {len(combined)})."
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate markdown files using LM Studio REST API (OpenAI-compatible)."
    )

    parser.add_argument(
        "--source-lang",
        type=str,
        default="en",
        help="Source language code (default: en).",
    )
    parser.add_argument(
        "--target-lang",
        type=str,
        required=True,
        help="Target language code (required), e.g. de, en, fr, es.",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="manuscript",
        help="Base directory to scan recursively for *.md (default: manuscript).",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Translate exactly one Markdown file (overrides --base-dir).",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("LM_STUDIO_API_URL", DEFAULT_API_URL),
        help=(
            "LM Studio chat completions endpoint "
            f"(default: {DEFAULT_API_URL}). Env: LM_STUDIO_API_URL"
        ),
    )
    parser.add_argument(
        "--models-url",
        type=str,
        default=os.getenv("LM_STUDIO_MODELS_URL", DEFAULT_MODELS_URL),
        help=(
            "LM Studio models endpoint used to auto-detect a default model "
            f"(default: {DEFAULT_MODELS_URL}). Env: LM_STUDIO_MODELS_URL"
        ),
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LM_STUDIO_MODEL", None),
        help=(
            "Optional explicit model id. If omitted, the first id from /v1/models is used. "
            "Env: LM_STUDIO_MODEL"
        ),
    )
    parser.add_argument(
        "--no-skip-html-tr",
        action="store_true",
        help="Disable default behavior that skips translating HTML <tr> blocks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing files and without updating .skiplist.",
    )

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    skiplist = load_skiplist(SKIPLIST_PATH)
    translated_files: set[str] = set()

    try:
        if args.file:
            translate_markdown_file(
                file_path=args.file,
                source_lang=args.source_lang,
                target_lang=args.target_lang,
                api_url=args.api_url,
                models_url=args.models_url,
                skiplist=skiplist,
                translated_files=translated_files,
                dry_run=args.dry_run,
                model=args.model,
                skip_html_tr_rows=(not args.no_skip_html_tr),
            )
        else:
            translate_markdown_files(
                base_dir=args.base_dir,
                source_lang=args.source_lang,
                target_lang=args.target_lang,
                api_url=args.api_url,
                models_url=args.models_url,
                skiplist=skiplist,
                translated_files=translated_files,
                dry_run=args.dry_run,
                model=args.model,
                skip_html_tr_rows=(not args.no_skip_html_tr),
            )
    except KeyboardInterrupt:
        print("\n🛑 Translation interrupted by user (Ctrl+C).")
    finally:
        if translated_files:
            print(f"📊 Files processed/marked: {len(translated_files)}")
        persist_skiplist(translated_files=translated_files, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
