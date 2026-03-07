# scripts/generate_audiobook.py
"""
Generate MP3 audio files from Markdown chapters or EPUB files using a pluggable TTS backend.

Pipeline:
1) Read input: either *.md files from a directory or chapters from an .epub file
2) Clean Markdown/HTML to TTS-friendly plain text (composed of small, testable steps)
3) Skip files that become empty (or contain no word characters) after cleanup
4) Synthesize speech to <output>/<stem>.mp3

Supported input formats:
- Directory with *.md files
- Single .epub file

Supported TTS engines:
- edge       -> Microsoft Edge Neural TTS (recommended, free, online)
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
from typing import List, Tuple

from scripts.tts.base import TTSAdapter

# Ensure imports work when script is run directly from "scripts/"
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")


# --- Default section order (same structure as full_export_book.py) -----------

DEFAULT_SECTION_ORDER = [
    "front-matter/toc.md",
    "front-matter/foreword.md",
    "front-matter/preface.md",
    "chapters",  # Entire chapters folder
    "back-matter/epilogue.md",
    "back-matter/glossary.md",
    "back-matter/acknowledgments.md",
    "back-matter/about-the-author.md",
    "back-matter/bibliography.md",
    "back-matter/imprint.md",
]


# --- Cleaning step functions -------------------------------------------------


def normalize_newlines(text: str) -> str:
    """Unify line endings: convert Windows and old Mac line breaks into '\\n'."""
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
    Also normalize non-breaking spaces to regular spaces for TTS/testing.
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


# --- EPUB extraction ---------------------------------------------------------


def extract_chapters_from_epub(
    epub_path: Path, skip_patterns: List[str] | None = None
) -> List[Tuple[str, str]]:
    """
    Extract chapters from an EPUB file as (chapter_name, html_content) pairs.

    Uses ebooklib to read the EPUB spine (reading order) and extracts
    only document items (XHTML content), skipping navigation, images, CSS, etc.

    :param epub_path: Path to the .epub file.
    :param skip_patterns: Optional list of case-insensitive keywords. Chapters whose
                          title or filename contains any of these patterns are skipped.
                          Example: ["toc", "cover", "imprint"]

    Returns a list of (chapter_name, raw_html_text) tuples.
    """
    from ebooklib import epub, ITEM_DOCUMENT
    from bs4 import BeautifulSoup

    book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
    patterns = [p.lower() for p in (skip_patterns or [])]

    chapters: List[Tuple[str, str]] = []
    chapter_idx = 0

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        body_content = item.get_body_content()
        if body_content is None:
            continue

        raw_html = body_content.decode("utf-8", errors="replace")
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator="\n")

        # Skip empty or near-empty chapters (cover pages, blank pages, etc.)
        if not text.strip() or not re.search(r"\w", text):
            continue

        # Try to extract a chapter title from the first heading
        heading = soup.find(re.compile(r"^h[1-3]$", re.IGNORECASE))
        if heading and heading.get_text(strip=True):
            title = heading.get_text(strip=True)
        else:
            title = item.get_name()

        # Apply skip patterns against title and filename
        if patterns:
            match_text = f"{title} {item.get_name()}".lower()
            if any(p in match_text for p in patterns):
                continue

        # Build a sortable filename prefix
        chapter_idx += 1
        safe_title = re.sub(r"[^\w\s-]", "", title)[:60].strip()
        chapter_name = (
            f"{chapter_idx:02d}_{safe_title}"
            if safe_title
            else f"{chapter_idx:02d}_chapter"
        )

        chapters.append((chapter_name, raw_html))

    return chapters


# --- TTS plumbing ------------------------------------------------------------


def get_tts_adapter(engine: str, lang: str, voice: str | None, rate: int) -> TTSAdapter:
    """
    Select the correct TTS adapter class depending on the chosen engine.
    - edge       -> Microsoft Edge Neural TTS (recommended, free, requires internet)
    - google     -> gTTS (requires internet)
    - pyttsx3    -> offline/local
    - elevenlabs -> ElevenLabs API (needs ELEVENLABS_API_KEY in environment)
    """
    if engine == "edge":
        from scripts.tts.edge_tts_adapter import EdgeTTSAdapter

        return EdgeTTSAdapter(lang=lang, voice=voice)
    elif engine == "google":
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


# --- Audio generation --------------------------------------------------------


def _clean_and_speak(
    name: str, raw_text: str, output_dir: Path, tts: TTSAdapter
) -> None:
    """Clean raw text (Markdown or HTML) and synthesize to MP3 if non-empty."""
    text = clean_markdown_for_tts(raw_text)
    if not text or not re.search(r"\w", text):
        return
    out_path = output_dir / f"{name}.mp3"
    print(f"Generating: {out_path.name}")
    tts.speak(text, out_path)


def collect_files_in_order(
    input_dir: Path, section_order: List[str]
) -> List[Tuple[str, Path]]:
    """
    Collect *.md files from input_dir according to section_order.

    Each entry in section_order is either:
    - A relative path to a specific .md file (e.g. 'front-matter/foreword.md')
    - A directory name (e.g. 'chapters') whose *.md files are included sorted

    Files that don't exist are silently skipped.
    Returns a list of (numbered_name, file_path) tuples.
    """
    files: List[Path] = []

    for entry in section_order:
        entry_path = input_dir / entry
        if entry_path.is_file():
            files.append(entry_path)
        elif entry_path.is_dir():
            files.extend(sorted(entry_path.glob("*.md")))
        # else: skip silently (file/dir doesn't exist in this project)

    # If section_order matched nothing, fall back to all *.md files recursively
    if not files:
        files = sorted(input_dir.rglob("*.md"))

    # Number them for correct playback order
    result: List[Tuple[str, Path]] = []
    for idx, f in enumerate(files, start=1):
        safe_stem = re.sub(r"[^\w\s-]", "", f.stem)[:60].strip()
        name = f"{idx:02d}_{safe_stem}" if safe_stem else f"{idx:02d}_chapter"
        result.append((name, f))

    return result


def generate_audio_from_markdown(
    input_dir: Path,
    output_dir: Path,
    tts: TTSAdapter,
    section_order: List[str] | None = None,
) -> None:
    """
    Convert *.md files in input_dir to MP3 files in output_dir,
    respecting section_order for correct book sequence.
    Skips any file whose cleaned text is empty or contains no word characters.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    order = section_order if section_order is not None else DEFAULT_SECTION_ORDER
    ordered_files = collect_files_in_order(input_dir, order)

    if not ordered_files:
        print(f"No *.md files found in {input_dir}")
        return

    print(f"Processing {len(ordered_files)} file(s) from {input_dir}")
    for name, md_file in ordered_files:
        raw_text = md_file.read_text(encoding="utf-8")
        _clean_and_speak(name, raw_text, output_dir, tts)


def list_chapters_from_epub(epub_path: Path) -> None:
    """Print all chapters found in the EPUB with index and title (for preview)."""
    chapters = extract_chapters_from_epub(epub_path)
    if not chapters:
        print(f"No readable chapters found in {epub_path.name}")
        return
    print(f"\nChapters in {epub_path.name}:\n")
    for name, _html in chapters:
        print(f"  {name}")
    print(f"\nTotal: {len(chapters)} chapter(s)")
    print("Use --skip to exclude chapters by keyword, e.g. --skip toc,cover,imprint")


def generate_audio_from_epub(
    epub_path: Path,
    output_dir: Path,
    tts: TTSAdapter,
    skip_patterns: List[str] | None = None,
) -> None:
    """
    Extract chapters from an EPUB file and convert each to an MP3.
    Skips chapters that are empty after cleanup (cover pages, etc.)
    and chapters matching any skip_patterns.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    chapters = extract_chapters_from_epub(epub_path, skip_patterns)

    if not chapters:
        print(f"No readable chapters found in {epub_path.name}")
        return

    print(f"Found {len(chapters)} chapter(s) in {epub_path.name}")
    for chapter_name, raw_html in chapters:
        _clean_and_speak(chapter_name, raw_html, output_dir, tts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate audiobook from Markdown files or EPUB"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input: directory with *.md files OR a single .epub file",
    )
    parser.add_argument("--output", type=Path, help="Output folder for audio files")
    parser.add_argument(
        "--engine",
        type=str,
        choices=["edge", "google", "pyttsx3", "elevenlabs"],
        default="edge",
        help="TTS engine to use (default: edge)",
    )
    parser.add_argument("--lang", type=str, help="Language code (e.g. 'en', 'de')")
    parser.add_argument("--voice", type=str, help="Voice ID or name")
    parser.add_argument("--rate", type=int, help="Speech rate (pyttsx3 only)")
    parser.add_argument(
        "--settings", type=Path, help="Path to JSON voice-settings file"
    )
    parser.add_argument(
        "--section-order",
        type=Path,
        help="Path to JSON file defining section order (list of relative paths). "
        "If not provided, uses DEFAULT_SECTION_ORDER.",
    )
    parser.add_argument(
        "--list-chapters",
        action="store_true",
        help="List all chapters in the EPUB without generating audio, then exit.",
    )
    parser.add_argument(
        "--skip",
        type=str,
        help="Comma-separated keywords to skip chapters whose title or filename "
        "matches (case-insensitive). Example: --skip toc,cover,imprint",
    )

    args = parser.parse_args()

    input_path = args.input

    # --list-chapters: preview EPUB contents and exit (no TTS needed)
    if args.list_chapters:
        if input_path.is_file() and input_path.suffix.lower() == ".epub":
            list_chapters_from_epub(input_path)
        else:
            print("--list-chapters is only supported for .epub files")
        return

    # --output is required for actual generation
    if not args.output:
        parser.error("--output is required when generating audio")

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

    # Load section order (optional)
    section_order = None
    if args.section_order and args.section_order.exists():
        with args.section_order.open("r", encoding="utf-8") as f:
            section_order = json.load(f)
    elif config.get("section_order"):
        section_order = config["section_order"]

    # Parse skip patterns from CLI or config
    skip_patterns = None
    if args.skip:
        skip_patterns = [s.strip() for s in args.skip.split(",") if s.strip()]
    elif config.get("skip"):
        skip_patterns = config["skip"]

    if input_path.is_file() and input_path.suffix.lower() == ".epub":
        generate_audio_from_epub(input_path, args.output, tts, skip_patterns)
    elif input_path.is_dir():
        generate_audio_from_markdown(input_path, args.output, tts, section_order)
    else:
        raise ValueError(
            f"--input must be a directory with *.md files or a .epub file, got: {input_path}"
        )


if __name__ == "__main__":
    main()
