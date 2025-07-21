# scripts/shortcuts_translate.py

import argparse
from scripts.translate_book_deepl import main as export_translate_book_deepl_main
import sys

# Supported language codes (extend as needed)
SUPPORTED_LANGS = {
    "EN": "English",
    "DE": "German",
    "ES": "Spanish",
    "FR": "French",
    "IT": "Italian",
    # Add more if needed
}

# --- Translation Shortcuts ---

def translate():
    """
    CLI command to translate a manuscript using DeepL
    Usage: poetry run translate --from EN --to DE --dir manuscript
    """
    parser = argparse.ArgumentParser(
        description="Translate a manuscript from one language to another using DeepL"
    )
    parser.add_argument(
        "--from", dest="source", required=True,
        choices=SUPPORTED_LANGS.keys(),
        help=f"Source language code ({', '.join(SUPPORTED_LANGS.keys())})"
    )
    parser.add_argument(
        "--to", dest="target", required=True,
        choices=SUPPORTED_LANGS.keys(),
        help=f"Target language code ({', '.join(SUPPORTED_LANGS.keys())})"
    )
    parser.add_argument(
        "--dir", dest="base_dir", default="manuscript",
        help="Directory containing Markdown files (default: manuscript)"
    )

    args = parser.parse_args()

    if args.source == args.target:
        print(f"❌ Source and target languages must differ: both are '{args.source}'")
        sys.exit(1)

    print(f"🌍 Translating from {SUPPORTED_LANGS[args.source]} → {SUPPORTED_LANGS[args.target]}")
    print(f"📂 Folder: {args.base_dir}\n")

    sys.argv = [
        "translate-book-deepl",
        "--base-dir", args.base_dir,
        "--source-lang", args.source,
        "--target-lang", args.target,
    ]
    export_translate_book_deepl_main()


def translate_manuscript(source: str, target: str, base_dir: str):
    """
    Shortcut: Translate a custom manuscript folder from source to target language

    :param source: Source language code (e.g., EN)
    :param target: Target language code (e.g., DE)
    :param base_dir: Directory containing Markdown files to translate
    """
    sys.argv = [
        "translate-book-deepl",
        "--base-dir", base_dir,
        "--source-lang", source,
        "--target-lang", target,
    ]
    export_translate_book_deepl_main()


def translate_manuscript_to_german():
    """
    Shortcut: Translate the default manuscript folder from English to German
    """
    translate_manuscript(source="EN", target="DE", base_dir="manuscript")


def translate_manuscript_from_german_to_english():
    """
    Shortcut: Translate the default manuscript folder from German to English
    """
    translate_manuscript(source="DE", target="EN", base_dir="manuscript")


def translate_manuscript_from_english_to_spanish():
    """
    Shortcut: Translate the default manuscript folder from English to Spanish
    """
    translate_manuscript(source="EN", target="ES", base_dir="manuscript")


def translate_manuscript_from_german_to_spanish():
    """
    Shortcut: Translate the default manuscript folder from German to Spanish
    """
    translate_manuscript(source="DE", target="ES", base_dir="manuscript")