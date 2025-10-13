# scripts/tts/pyttsx3_adapter.py
import pyttsx3
from pathlib import Path
from scripts.tts.base import TTSAdapter
from typing import Optional


class Pyttsx3Adapter(TTSAdapter):
    def __init__(self, voice: Optional[str] = None, rate: int = 180):
        self.engine = pyttsx3.init()
        if voice:
            self.engine.setProperty("voice", voice)
        self.engine.setProperty("rate", rate)

    def speak(self, text: str, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine.save_to_file(text, str(output_path))
        self.engine.runAndWait()
