# scripts/tts/edge_tts_adapter.py
"""
Edge TTS adapter using Microsoft Edge's online neural TTS service.

Requires:
    poetry add edge-tts

No API key needed. Requires internet connection.

Splits long texts into chunks to avoid WebSocket timeouts on Microsoft's service.

German voices (examples):
    de-DE-KatjaNeural    (female, Germany)
    de-DE-ConradNeural   (male, Germany)
    de-AT-IngridNeural   (female, Austria)
    de-AT-JonasNeural    (male, Austria)
    de-CH-LeniNeural     (female, Switzerland)
    de-CH-JanNeural      (male, Switzerland)

English voices (examples):
    en-US-JennyNeural    (female, US)
    en-US-GuyNeural      (male, US)
    en-GB-SoniaNeural    (female, UK)
    en-GB-RyanNeural     (male, UK)

List all voices: edge-tts --list-voices
"""

import asyncio
import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from scripts.tts.base import TTSAdapter

# Maximum characters per TTS request. Edge TTS can handle ~5000 chars reliably,
# but shorter chunks are more robust against WebSocket timeouts.
_MAX_CHUNK_CHARS = 4000

# Default voices per language code
_DEFAULT_VOICES = {
    "de": "de-DE-KatjaNeural",
    "de-de": "de-DE-KatjaNeural",
    "de-at": "de-AT-IngridNeural",
    "de-ch": "de-CH-LeniNeural",
    "en": "en-US-JennyNeural",
    "en-us": "en-US-JennyNeural",
    "en-gb": "en-GB-SoniaNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "el": "el-GR-AthinaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
}


def _split_text_into_chunks(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> List[str]:
    """
    Split text into chunks that respect paragraph and sentence boundaries.

    Strategy:
    1. Split by double newlines (paragraphs)
    2. If a paragraph is still too long, split by sentences
    3. If a sentence is still too long, hard-split at max_chars
    """
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: List[str] = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph stays within limit, accumulate
        candidate = f"{current_chunk}\n\n{para}" if current_chunk else para
        if len(candidate) <= max_chars:
            current_chunk = candidate
            continue

        # Flush current chunk if non-empty
        if current_chunk:
            chunks.append(current_chunk)
            current_chunk = ""

        # If the paragraph itself fits, start a new chunk with it
        if len(para) <= max_chars:
            current_chunk = para
            continue

        # Paragraph too long: split by sentences
        sentences = re.split(r"(?<=[.!?])\s+", para)
        for sentence in sentences:
            if not sentence.strip():
                continue
            candidate = f"{current_chunk} {sentence}" if current_chunk else sentence
            if len(candidate) <= max_chars:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # Hard-split if a single sentence exceeds max_chars
                if len(sentence) > max_chars:
                    for i in range(0, len(sentence), max_chars):
                        chunks.append(sentence[i : i + max_chars])
                    current_chunk = ""
                else:
                    current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class EdgeTTSAdapter(TTSAdapter):
    """
    TTS adapter backed by Microsoft Edge's neural TTS service (free, online).

    Automatically splits long texts into chunks to avoid WebSocket timeouts.

    :param lang: Language code (e.g. 'de', 'en', 'es', 'fr', 'el').
                 Used to pick a default voice if none is specified.
    :param voice: Full Edge TTS voice name, e.g. 'de-DE-ConradNeural'.
                  Overrides the language-based default.
    :param rate: Speech rate adjustment, e.g. '+0%', '-10%', '+20%'.
    :param volume: Volume adjustment, e.g. '+0%', '-20%'.
    :param pitch: Pitch adjustment, e.g. '+0Hz', '-5Hz'.
    """

    def __init__(
        self,
        lang: str = "de",
        voice: Optional[str] = None,
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
    ):
        self.voice = voice or _DEFAULT_VOICES.get(lang.lower(), "en-US-JennyNeural")
        self.rate = rate
        self.volume = volume
        self.pitch = pitch

    def speak(self, text: str, output_path: Path) -> None:
        """Convert text to speech and save as MP3."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = _split_text_into_chunks(text)
        if not chunks:
            return

        if len(chunks) == 1:
            # Single chunk: generate directly to output
            self._run_async(self._generate_single(chunks[0], output_path))
        else:
            # Multiple chunks: generate each, then concatenate
            self._run_async(self._generate_chunked(chunks, output_path))

    @staticmethod
    def _run_async(coro) -> None:
        """Run an async coroutine, handling existing event loops gracefully."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an existing event loop (e.g. Jupyter, nested calls)
            try:
                import nest_asyncio

                nest_asyncio.apply()
                loop.run_until_complete(coro)
            except ImportError:
                # Fallback: create a new loop in a thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, coro).result()
        else:
            asyncio.run(coro)

    async def _generate_single(self, text: str, output_path: Path) -> None:
        """Generate a single chunk to an MP3 file with retry."""
        await self._tts_with_retry(text, output_path)

    async def _tts_with_retry(
        self, text: str, output_path: Path, max_retries: int = 3
    ) -> None:
        """Call Edge TTS with retry on failure."""
        import edge_tts

        for attempt in range(1, max_retries + 1):
            try:
                communicate = edge_tts.Communicate(
                    text,
                    self.voice,
                    rate=self.rate,
                    volume=self.volume,
                    pitch=self.pitch,
                )
                await communicate.save(str(output_path))
                return
            except Exception as exc:
                if attempt < max_retries:
                    wait = attempt * 2
                    print(f"    Retry {attempt}/{max_retries} after error: {exc}")
                    print(f"    Waiting {wait}s before next attempt...")
                    await asyncio.sleep(wait)
                else:
                    raise RuntimeError(
                        f"Edge TTS failed after {max_retries} attempts: {exc}"
                    ) from exc

    async def _generate_chunked(self, chunks: List[str], output_path: Path) -> None:
        """Generate multiple chunks, concatenate into final MP3."""
        temp_files: List[Path] = []
        temp_dir = Path(tempfile.mkdtemp(prefix="edge_tts_"))

        try:
            for idx, chunk in enumerate(chunks):
                temp_path = temp_dir / f"chunk_{idx:04d}.mp3"
                print(f"    Chunk {idx + 1}/{len(chunks)} ({len(chunk)} chars)")
                await self._tts_with_retry(chunk, temp_path)
                temp_files.append(temp_path)

            # Concatenate all MP3 chunks (MP3 is concatenable by nature)
            with open(output_path, "wb") as outfile:
                for temp_file in temp_files:
                    outfile.write(temp_file.read_bytes())

        finally:
            # Clean up entire temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
