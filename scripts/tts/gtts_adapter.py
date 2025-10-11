# scripts/tts/gtts_adapter.py
from gtts import gTTS
from pathlib import Path
from scripts.tts.base import TTSAdapter


class GoogleTTSAdapter(TTSAdapter):
    def __init__(self, lang: str = "en"):
        self.lang = lang

    def speak(self, text: str, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text=text, lang=self.lang)
        tts.save(str(output_path))
