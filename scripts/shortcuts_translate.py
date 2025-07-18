# scripts/shortcuts_translate.py

import sys
from scripts.translate_book_deepl import main as export_translate_book_deepl_main

# --- Translation Shortcuts ---


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
    Shortcut: Translate the default manuscript folder from English to German
    """
    translate_manuscript(source="DE", target="EN", base_dir="manuscript")
