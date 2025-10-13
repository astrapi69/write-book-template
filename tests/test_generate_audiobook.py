# tests/test_generate_audiobook.py

from types import ModuleType
import sys
from scripts.tts.base import TTSAdapter
from pathlib import Path

from scripts.generate_audiobook import generate_audio_from_markdown, get_tts_adapter


class DummyTTS(TTSAdapter):
    def __init__(self) -> None:
        self.calls: list[tuple[str, Path]] = []

    def speak(self, text: str, output_path: Path) -> None:
        self.calls.append((text, output_path))
        output_path.write_bytes(b"\x00")


def write(p: Path, s: str):
    p.write_text(s, encoding="utf-8")


def test_generate_skips_empty_after_cleanup(tmp_path: Path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    write(
        src / "01.md", "<figure><img src='x.png'/><figcaption>c</figcaption></figure>"
    )
    write(src / "02.md", "Hello **world** [link](https://e.x)")

    tts = DummyTTS()
    generate_audio_from_markdown(src, out, tts)

    files = sorted(p.name for p in out.glob("*.mp3"))
    assert files == ["02.mp3"]
    assert len(tts.calls) == 1
    assert "Hello world link" in tts.calls[0][0]


def test_output_directory_is_created(tmp_path: Path):
    src = tmp_path / "src"
    out = tmp_path / "nested" / "audio"
    src.mkdir()
    write(src / "chapter.md", "# Title\nSome text.")

    tts = DummyTTS()
    generate_audio_from_markdown(src, out, tts)
    assert (out / "chapter.mp3").exists()


def test_generate_skips_meaningless_text(tmp_path: Path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    # After cleanup this is only punctuation/newlines → should skip
    write(src / "x.md", "![i](a.png)\n<figure>...</figure>\n(**)**\n")
    tts = DummyTTS()
    generate_audio_from_markdown(src, out, tts)
    assert list(out.glob("*.mp3")) == []
    assert tts.calls == []


# --- get_tts_adapter coverage: fake adapter modules so we don't need real deps


def _install_fake_adapter_module(
    module_name: str, class_name: str, raises_on_kwargs=None
):
    """
    Install a minimal fake adapter module into sys.modules:
    module_name (e.g., 'scripts.tts.gtts_adapter') containing class_name
    (e.g., 'GoogleTTSAdapter') with .speak() that writes bytes.
    If raises_on_kwargs is provided (callable), it may raise in __init__.
    """
    mod = ModuleType(module_name)

    class _FakeAdapter:
        def __init__(self, *args, **kwargs):
            if raises_on_kwargs and raises_on_kwargs(kwargs):
                raise ValueError("Missing API key")
            self.kwargs = kwargs

        def speak(self, text, output_path: Path):
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(b"FAKE_MP3")

    setattr(mod, class_name, _FakeAdapter)
    sys.modules[module_name] = mod


def test_get_tts_adapter_google(monkeypatch):
    _install_fake_adapter_module("scripts.tts.gtts_adapter", "GoogleTTSAdapter")
    adapter = get_tts_adapter("google", lang="en", voice=None, rate=200)
    assert hasattr(adapter, "speak")


def test_get_tts_adapter_pyttsx3(monkeypatch):
    _install_fake_adapter_module("scripts.tts.pyttsx3_adapter", "Pyttsx3Adapter")
    adapter = get_tts_adapter("pyttsx3", lang="en", voice="Alice", rate=180)
    assert hasattr(adapter, "speak")


def test_get_tts_adapter_elevenlabs_with_and_without_key(monkeypatch):
    # Fake ElevenLabs adapter that raises if api_key missing
    def raises_on_kwargs(kwargs):
        return not kwargs.get("api_key")

    _install_fake_adapter_module(
        "scripts.tts.elevenlabs_adapter", "ElevenLabsAdapter", raises_on_kwargs
    )

    # Without key -> should raise
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    try:
        raised = False
        get_tts_adapter("elevenlabs", lang="en", voice=None, rate=200)
    except ValueError:
        raised = True
    assert raised, "Expected ValueError when ELEVENLABS_API_KEY is missing"

    # With key -> should construct
    monkeypatch.setenv("ELEVENLABS_API_KEY", "XYZ")
    adapter = get_tts_adapter("elevenlabs", lang="en", voice="Rachel", rate=200)
    assert hasattr(adapter, "speak")


def test_get_tts_adapter_invalid_engine():
    try:
        get_tts_adapter("unknown", lang="en", voice=None, rate=200)
        assert False, "Expected ValueError for invalid engine"
    except ValueError:
        pass
