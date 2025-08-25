# scripts/generate_audiobook.py
"""
Generate MP3 audio files from Markdown chapters using a pluggable TTS backend.

Pipeline:
1) Read each *.md file from an input directory
2) Clean Markdown/HTML to TTS-friendly plain text
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
import argparse
from pathlib import Path
from scripts.tts.base import TTSAdapter

# ⚠️ If this script lives in scripts/, this change ensures relative imports work
# when executed directly. If your tooling prefers not to mutate CWD on import,
# consider moving this into `main()` behind a guard.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")


def clean_markdown_for_tts(markdown_text: str) -> str:
    """
    Normalize Markdown/HTML to plain text suitable for TTS.

    What it does:
    - Normalizes line endings
    - Removes YAML front matter
    - Removes <figure> blocks (and stray <figcaption>)
    - Removes HTML comments
    - Strips Markdown images and turns links into their link text
    - Removes reference-style links and link definition lines
    - Removes Markdown emphasis markers (bold/italic) but keeps text
    - Removes heading markers (#) but keeps titles
    - Removes fenced code blocks and backticks from inline code (keeps code text)
    - Strips remaining HTML tags
    - Removes Markdown table rows (| ... |)
    - Collapses excessive blank lines
    - Unescapes HTML entities (&nbsp;, &amp;, …)
    """
    text = markdown_text.replace("\r\n", "\n").replace("\r", "\n")

    # --- Front matter (YAML) -------------------------------------------------
    # At start of file: ---\n ... \n---\n
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)

    # --- HTML blocks / comments ----------------------------------------------
    # Full <figure>...</figure> (captures nested <img>/<figcaption>)
    text = re.sub(r'<figure\b[^>]*>.*?</figure>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Defensive: stray <figcaption>...</figcaption>
    text = re.sub(r'<figcaption\b[^>]*>.*?</figcaption>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # --- Images & Links -------------------------------------------------------
    # Markdown image: ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Inline link: [text](url)  -> keep "text"
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Reference link usage: [text][id] or [text][] -> keep "text"
    text = re.sub(r'\[([^\]]+)\]\s*\[[^\]]*\]', r'\1', text)
    # Link definition lines: [id]: http...
    text = re.sub(r'^\s*\[[^\]]+\]:\s*\S+.*$', '', text, flags=re.MULTILINE)
    # Defensive: stray empty link definition keys
    text = re.sub(r'^\s*\[[^\]]+\]:\s*$', '', text, flags=re.MULTILINE)

    # --- Emphasis / Headings --------------------------------------------------
    # Bold/italic markers (**text**, *text*, __text__, _text_) -> keep text
    text = re.sub(r'(\*\*|\*|__|_)(.*?)\1', r'\2', text)
    # Heading markers: "# "..." -> keep the title text
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # --- Code blocks / inline code -------------------------------------------
    # Fenced code blocks: ``` ... ```  or  ~~~ ... ~~~
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'~~~.*?~~~', '', text, flags=re.DOTALL)
    # Inline code: `code` -> keep "code" without backticks
    text = re.sub(r'`(.+?)`', r'\1', text)

    # --- Residual HTML tags ---------------------------------------------------
    text = re.sub(r'<[^>]+>', '', text)

    # --- Tables (Markdown) ----------------------------------------------------
    # Remove table rows / separators
    text = re.sub(r'^\s*\|.*\|\s*$', '', text, flags=re.MULTILINE)

    # --- Whitespace and entities ---------------------------------------------
    # Collapse 3+ newlines -> 2 newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Unescape HTML entities (&nbsp; -> space, &amp; -> &)
    text = html.unescape(text)

    return text.strip()


def get_tts_adapter(engine: str, lang: str, voice: str | None, rate: int) -> TTSAdapter:
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


def generate_audio_from_markdown(input_dir: Path, output_dir: Path, tts: TTSAdapter) -> None:
    """
    Convert all *.md files in input_dir to MP3 files in output_dir using the given TTS adapter.
    Skips any file whose cleaned text is empty or contains no word characters.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(input_dir.glob("*.md")):
        raw_text = md_file.read_text(encoding="utf-8")
        text = clean_markdown_for_tts(raw_text)

        # Skip if nothing meaningful is left for TTS
        if not text or not re.search(r'\w', text):
            continue

        out_path = output_dir / f"{md_file.stem}.mp3"
        print(f"Generating: {out_path.name}")
        tts.speak(text, out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate audiobook from markdown files")
    parser.add_argument("--input", type=Path, required=True, help="Input folder with markdown files")
    parser.add_argument("--output", type=Path, required=True, help="Output folder for audio files")
    parser.add_argument("--lang", type=str, default="en", help="Language code (e.g. 'en', 'de')")
    parser.add_argument("--voice", type=str, default=None, help="Voice ID or name (pyttsx3/ElevenLabs)")
    parser.add_argument("--rate", type=int, default=200, help="Speech rate (pyttsx3 only)")
    parser.add_argument(
        "--engine",
        type=str,
        choices=["google", "pyttsx3", "elevenlabs"],
        default="google",
        help="TTS engine to use",
    )

    args = parser.parse_args()
    tts = get_tts_adapter(args.engine, args.lang, args.voice, args.rate)
    generate_audio_from_markdown(args.input, args.output, tts)


if __name__ == "__main__":
    main()
