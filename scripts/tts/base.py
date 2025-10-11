# scripts/tts/base.py
from abc import ABC, abstractmethod
from pathlib import Path


class TTSAdapter(ABC):
    @abstractmethod
    def speak(self, text: str, output_path: Path):
        """Convert text to speech and save it to output_path"""
        pass
