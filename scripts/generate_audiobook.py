# scripts/generate_audiobook.py
import os
import argparse
from pathlib import Path
from scripts.tts.base import TTSAdapter

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")
import re


def clean_markdown_for_tts(markdown_text: str) -> str:
    """
    Normalize Markdown/HTML to plain text suitable for TTS.
    Removes figures, images, links (keeps link text), formatting, code, tables, etc.
    """
    text = markdown_text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove full <figure>...</figure> blocks (including nested img/figcaption)
    text = re.sub(r'<figure\b[^>]*>.*?</figure>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Defensive: remove standalone figcaptions if present outside figure
    text = re.sub(r'<figcaption\b[^>]*>.*?</figcaption>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Remove images ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # Remove links [text](url) → keep only "text"
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Reference links: [text][id] and [text][]
    text = re.sub(r'\[([^\]]+)\]\s*\[[^\]]*\]', r'\1', text)
    # Remove link definition lines: [id]: http...
    text = re.sub(r'^\s*\[[^\]]+\]:\s*\S+.*$', '', text, flags=re.MULTILINE)

    # Remove bold/italic markdown: **text**, *text*, __text__, _text_
    text = re.sub(r'(\*\*|\*|__|_)(.*?)\1', r'\2', text)

    # Remove headings (#) but keep the text
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # Remove code blocks (```\n...\n```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Remove inline code `code`
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove table rows (Markdown-style)
    text = re.sub(r'^\s*\|.*\|\s*$', '', text, flags=re.MULTILINE)

    # Remove stray link definition blocks that may remain after edits
    text = re.sub(r'^\s*\[[^\]]+\]:\s*$', '', text, flags=re.MULTILINE)

    # Remove multiple empty lines (collapse to max 2 newlines), and strip leading/trailing whitespace
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    return text


def get_tts_adapter(engine: str, lang: str, voice: str, rate: int) -> TTSAdapter:
    if engine == "google":
        from scripts.tts.gtts_adapter import GoogleTTSAdapter
        return GoogleTTSAdapter(lang=lang)
    elif engine == "pyttsx3":
        from scripts.tts.pyttsx3_adapter import Pyttsx3Adapter
        return Pyttsx3Adapter(voice=voice, rate=rate)
    elif engine == "elevenlabs":
        from scripts.tts.elevenlabs_adapter import ElevenLabsAdapter
        api_key = os.getenv("ELEVENLABS_API_KEY")
        return ElevenLabsAdapter(api_key=api_key, voice=voice, lang=lang)
    else:
        raise ValueError(f"Unsupported engine: {engine}")


def generate_audio_from_markdown(input_dir: Path, output_dir: Path, tts: TTSAdapter):
    output_dir.mkdir(parents=True, exist_ok=True)
    for md_file in sorted(input_dir.glob("*.md")):
        raw_text = md_file.read_text(encoding="utf-8")
        text = clean_markdown_for_tts(raw_text)
        if not text.strip():
            # skip empty after cleanup
            continue
        out_path = output_dir / f"{md_file.stem}.mp3"
        print(f"Generating: {out_path.name}")
        tts.speak(text, out_path)


def main():
    parser = argparse.ArgumentParser(description="Generate audiobook from markdown files")
    parser.add_argument("--input", type=Path, required=True, help="Input folder with markdown files")
    parser.add_argument("--output", type=Path, required=True, help="Output folder for audio files")
    parser.add_argument("--lang", type=str, default="en", help="Language code (e.g. 'en', 'de')")
    parser.add_argument("--voice", type=str, default=None, help="Voice ID or name (pyttsx3 only)")
    parser.add_argument("--rate", type=int, default=200, help="Speech rate (pyttsx3 only)")
    parser.add_argument("--engine", type=str, choices=["google", "pyttsx3", "elevenlabs"], default="google",
                        help="TTS engine to use")

    args = parser.parse_args()
    tts = get_tts_adapter(args.engine, args.lang, args.voice, args.rate)
    generate_audio_from_markdown(args.input, args.output, tts)


if __name__ == "__main__":
    main()