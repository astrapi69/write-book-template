# scripts/tts/fish_audio.py
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from .base import TTSAdapter


class FishAudioTTS(TTSAdapter):
    """
    Fish Audio (cloud) TTS Adapter.

    Requires an API key and either a `reference_id` (pre-trained / cloned voice on Fish Audio)
    or `references` (list of dicts with inline reference audio config if you use msgpack route).

    Basic JSON mode here uses `reference_id`.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = "https://api.fish.audio",
        api_version: str = "v1",
        model: str = "speech-1.5",
        reference_id: Optional[str] = None,
        audio_format: str = "mp3",
        extra_headers: Optional[Dict[str, str]] = None,
        default_params: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
    ):
        """
        :param api_key: Fish Audio API key (or set env FISHAUDIO_API_KEY)
        :param base_url: API base, e.g. https://api.fish.audio
        :param api_version: API version path segment, default 'v1'
        :param model: model name, e.g. 'speech-1.5'
        :param reference_id: your cloned/pre-trained voice id on Fish Audio
        :param audio_format: 'mp3' | 'wav' | 'opus' ...
        :param extra_headers: optional extra headers
        :param default_params: optional dict merged into request JSON (e.g. speed, volume, emotion)
        :param timeout: request timeout (s)
        """
        self.api_key = api_key or os.getenv("FISHAUDIO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FishAudioTTS: API key missing. Set `api_key` or env FISHAUDIO_API_KEY."
            )

        self.base_url = base_url.rstrip("/")
        self.api_version = api_version.strip("/")
        self.model = model
        self.reference_id = reference_id
        self.audio_format = audio_format
        self.extra_headers = extra_headers or {}
        self.default_params = default_params or {}
        self.timeout = timeout

        # Known endpoint from Fish Audio dev docs:
        # curl -X POST https://api.fish.audio/v1/tts -H "Authorization: Bearer ..." -H "model: speech-1.5" ...
        # https://fish.audio/developers/  (shows example)  /  https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech
        self.endpoint = f"{self.base_url}/{self.api_version}/tts"

    def speak(self, text: str, output_path: Path):
        """
        Convert text to speech via Fish Audio and save to output_path.
        """
        if not text or not text.strip():
            raise ValueError("FishAudioTTS.speak: `text` must not be empty.")

        if not self.reference_id:
            # You can also use 'references' (inline reference audio) with MessagePack,
            # but JSON + reference_id is the simplest path for now.
            raise ValueError(
                "FishAudioTTS.speak: `reference_id` is required for JSON mode. "
                "Create/choose a voice on Fish Audio and pass its id."
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Some examples show a dedicated 'model' header
            "model": self.model,
            **self.extra_headers,
        }

        payload: Dict[str, Any] = {
            "text": text,
            "reference_id": self.reference_id,
            "format": self.audio_format,
            # optional params (examples): speed, volume, emotion, seed, sample_rate, normalize, etc.
            **self.default_params,
        }

        with requests.post(
            self.endpoint,
            headers=headers,
            data=json.dumps(payload),
            stream=True,
            timeout=self.timeout,
        ) as resp:
            if resp.status_code != 200:
                # Try to expose server error details
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                raise RuntimeError(
                    f"FishAudioTTS API error [{resp.status_code}]: {detail}"
                )

            # Write streamed audio to file
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return output_path
