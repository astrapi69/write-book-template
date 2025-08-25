# tests/test_generate_audiobook.py
from pathlib import Path
from types import SimpleNamespace
from scripts.generate_audiobook import generate_audio_from_markdown


class DummyTTS:
    def __init__(self):
        self.calls = []

    def speak(self, text, out_path: Path):
        # record and simulate an output file
        self.calls.append((text, Path(out_path)))
        Path(out_path).write_bytes(b"FAKE_MP3")


def write(p: Path, s: str):
    p.write_text(s, encoding="utf-8")


def test_generate_skips_empty_after_cleanup(tmp_path: Path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    # This file becomes empty after cleanup (only image + figure)
    write(src / "01.md", "<figure><img src='x.png'/><figcaption>c</figcaption></figure>")
    # This file contains real text
    write(src / "02.md", "Hello **world** [link](https://e.x)")

    tts = DummyTTS()
    generate_audio_from_markdown(src, out, tts)

    # Only the second should be generated
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