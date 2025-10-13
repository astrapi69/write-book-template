# scripts/generate_audiobook.py
"""
Generate MP3 audio files from Markdown chapters using a pluggable TTS backend.

Pipeline:
1) Read each *.md file from an input directory
2) Clean Markdown/HTML to TTS-friendly plain text (composed of small, testable steps)
3) Skip files that become empty (or contain no word characters) after cleanup
4) Synthesize speech to <output>/<stem>.mp3

Supported TTS engines:
- google     -> gTTS (online)
- pyttsx3    -> offline/local TTS
- elevenlabs -> ElevenLabs API (requires ELEVENLABS_API_KEY)
"""

import os
import re
import html
import json
import argparse
from pathlib import Path
from scripts.tts.base import TTSAdapter

# Ensure imports work when script is run directly from "scripts/"
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")


# --- Cleaning step functions -------------------------------------------------


def normalize_newlines(text: str) -> str:
    """Unify line endings: convert Windows and old Mac line breaks into '\n'."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_yaml_front_matter(text: str) -> str:
    """Remove YAML front matter blocks (--- ... ---) often found at file start."""
    return re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)


def remove_figure_blocks(text: str) -> str:
    """Remove entire <figure>...</figure> blocks and stray <figcaption> tags."""
    text = re.sub(
        r"<figure\b[^>]*>.*?</figure>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(
        r"<figcaption\b[^>]*>.*?</figcaption>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return text


def remove_html_comments(text: str) -> str:
    """Strip out HTML comments like <!-- hidden stuff -->."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def remove_markdown_images(text: str) -> str:
    """Remove Markdown inline images: ![alt](url)."""
    return re.sub(r"!\[.*?\]\(.*?\)", "", text)


def convert_inline_links_keep_text(text: str) -> str:
    """Convert [text](url) into just 'text', dropping the URL."""
    return re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)


def remove_reference_links_and_definitions(text: str) -> str:
    """Remove reference links [text][id] and link definitions [id]: url."""
    text = re.sub(r"\[([^\]]+)\]\s*\[[^\]]*\]", r"\1", text)  # [text][id] -> text
    text = re.sub(
        r"^\s*\[[^\]]+\]:\s*\S+.*$", "", text, flags=re.MULTILINE
    )  # definition lines
    text = re.sub(r"^\s*\[[^\]]+\]:\s*$", "", text, flags=re.MULTILINE)  # empty defs
    return text


def strip_emphasis_markers(text: str) -> str:
    """Remove Markdown emphasis markers (**bold**, *italic*, __strong__)."""
    return re.sub(r"(\*\*|\*|__|_)(.*?)\1", r"\2", text)


def strip_heading_markers(text: str) -> str:
    """Remove Markdown heading markers (#, ##, ...) but keep the heading text."""
    return re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)


def strip_fenced_code_blocks(text: str) -> str:
    """Remove fenced code blocks (``` ... ``` or ~~~ ... ~~~)."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.DOTALL)
    return text


def strip_inline_code_backticks(text: str) -> str:
    """Remove backticks from inline code `like this` but keep the content."""
    return re.sub(r"`(.+?)`", r"\1", text)


def strip_remaining_html_tags(text: str) -> str:
    """Remove any leftover HTML tags like <p>, <em>, <div>."""
    return re.sub(r"<[^>]+>", "", text)


def remove_markdown_tables(text: str) -> str:
    """Remove Markdown table rows (lines starting and ending with '|')."""
    return re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.MULTILINE)


def collapse_blank_lines(text: str) -> str:
    """Collapse 3 or more consecutive newlines into just 2."""
    return re.sub(r"\n{3,}", "\n\n", text)


def unescape_html_entities(text: str) -> str:
    """Convert HTML entities (&nbsp;, &amp;, etc.) into plain characters.
    Also normalize non‑breaking spaces to regular spaces for TTS/testing.
    """
    text = html.unescape(text)
    # Normalize common non-breaking/Unicode spaces to regular space
    text = text.replace("\u00a0", " ").replace("\u202f", " ").replace("\u2007", " ")
    # Collapse 2+ spaces -> single space (keeps newlines)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text


# --- Public cleaner composed of the steps -----------------------------------


def clean_markdown_for_tts(markdown_text: str) -> str:
    """
    Run all cleaning steps to normalize Markdown/HTML into plain text suitable for TTS.
    """
    text = normalize_newlines(markdown_text)
    text = remove_yaml_front_matter(text)
    text = remove_figure_blocks(text)
    text = remove_html_comments(text)

    text = remove_markdown_images(text)
    text = convert_inline_links_keep_text(text)
    text = remove_reference_links_and_definitions(text)

    text = strip_emphasis_markers(text)
    text = strip_heading_markers(text)

    text = strip_fenced_code_blocks(text)
    text = strip_inline_code_backticks(text)

    text = strip_remaining_html_tags(text)
    text = remove_markdown_tables(text)

    text = collapse_blank_lines(text)
    text = unescape_html_entities(text)

    return text.strip()


# --- TTS plumbing ------------------------------------------------------------


def get_tts_adapter(engine: str, lang: str, voice: str | None, rate: int) -> TTSAdapter:
    """
    Select the correct TTS adapter class depending on the chosen engine.
    - google     -> gTTS (requires internet)
    - pyttsx3    -> offline/local
    - elevenlabs -> ElevenLabs API (needs ELEVENLABS_API_KEY in environment)
    """
    if engine == "google":
        from scripts.tts.gtts_adapter import GoogleTTSAdapter

        return GoogleTTSAdapter(lang=lang)
    elif engine == "pyttsx3":
        from scripts.tts.pyttsx3_adapter import Pyttsx3Adapter

        return Pyttsx3Adapter(voice=voice, rate=rate)
    elif engine == "elevenlabs":
        from scripts.tts.elevenlabs_adapter import ElevenLabsAdapter

        api_key = os.getenv("ELEVENLABS_API_KEY")
        return ElevenLabsAdapter(api_key=api_key or "", voice=voice or "", lang=lang)
    else:
        raise ValueError(f"Unsupported engine: {engine}")


def generate_audio_from_markdown(
    input_dir: Path, output_dir: Path, tts: TTSAdapter
) -> None:
    """
    Convert all *.md files in input_dir to MP3 files in output_dir using the given TTS adapter.
    - Skips any file whose cleaned text is empty or contains no word characters.
    - Creates the output directory if it doesn’t exist.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(input_dir.glob("*.md")):
        raw_text = md_file.read_text(encoding="utf-8")
        text = clean_markdown_for_tts(raw_text)

        # Skip if nothing meaningful is left for TTS
        if not text or not re.search(r"\w", text):
            continue

        out_path = output_dir / f"{md_file.stem}.mp3"
        print(f"Generating: {out_path.name}")
        tts.speak(text, out_path)


def main():
    parser = argparse.ArgumentParser(
        description="Generate audiobook from markdown files"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input folder with markdown files"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output folder for audio files"
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=["google", "pyttsx3", "elevenlabs"],
        default="google",
        help="TTS engine to use",
    )
    parser.add_argument("--lang", type=str, help="Language code (e.g. 'en', 'de')")
    parser.add_argument("--voice", type=str, help="Voice ID or name")
    parser.add_argument("--rate", type=int, help="Speech rate (pyttsx3 only)")
    parser.add_argument(
        "--settings", type=Path, help="Path to JSON voice-settings file"
    )

    args = parser.parse_args()

    # Load settings from JSON (optional)
    config = {}
    if args.settings and args.settings.exists():
        with args.settings.open("r", encoding="utf-8") as f:
            config = json.load(f)

    # Apply CLI args (override config file if set)
    lang = args.lang or config.get("language", "en")
    voice = args.voice or config.get("voice", None)
    rate = args.rate if args.rate is not None else config.get("rate", 200)

    tts = get_tts_adapter(args.engine, lang=lang, voice=voice, rate=rate)
    generate_audio_from_markdown(args.input, args.output, tts)


if __name__ == "__main__":
    main()
