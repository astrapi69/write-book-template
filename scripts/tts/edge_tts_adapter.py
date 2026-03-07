# scripts/tts/edge_tts_adapter.py
"""
Edge TTS adapter using Microsoft Edge's online neural TTS service.

Requires:
    poetry add edge-tts

No API key needed. Requires internet connection.

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
from pathlib import Path
from typing import Optional

from scripts.tts.base import TTSAdapter

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


class EdgeTTSAdapter(TTSAdapter):
    """
    TTS adapter backed by Microsoft Edge's neural TTS service (free, online).

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
        asyncio.run(self._generate(text, output_path))

    async def _generate(self, text: str, output_path: Path) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
        )
        await communicate.save(str(output_path))
