# scripts/tts/elevenlabs_adapter.py
from elevenlabs import generate, save, set_api_key
from pathlib import Path
from scripts.tts.base import TTSAdapter


class ElevenLabsAdapter(TTSAdapter):
    def __init__(
        self,
        api_key: str,
        voice: str = "Rachel",
        model: str = "eleven_multilingual_v2",
        lang: str = "en",
    ):
        if not api_key:
            raise ValueError("ElevenLabs API key must be provided")
        set_api_key(api_key)
        self.voice = voice
        self.model = model
        self.lang = lang

    def speak(self, text: str, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio = generate(text=text, voice=self.voice, model=self.model)
        save(audio, str(output_path))
