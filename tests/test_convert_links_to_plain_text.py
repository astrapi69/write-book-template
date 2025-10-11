# tests/test_convert_links_to_plain_text.py
from pathlib import Path
from scripts.convert_links_to_plain_text import (
    convert_links_in_text,
    convert_file,
    convert_many,
)


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_basic_link_conversion():
    text = "Visit [Example](https://example.com) now."
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out == "Visit Example: https://example.com now."


def test_skip_images_and_anchor_links():
    text = "![Img](pic.png) and [anchor](#section)"
    out, n = convert_links_in_text(text)
    assert n == 0
    assert out == text


def test_skip_links_in_code():
    code = "```\n[Link](https://secret.com)\n``` and `[Another](https://skip.com)`"
    out, n = convert_links_in_text(code)
    assert n == 0
    assert "[Link]" in out
    assert "[Another]" in out


def test_file_and_many_conversion(tmp_path: Path):
    f1 = tmp_path / "file1.md"
    f2 = tmp_path / "file2.md"
    write(f1, "Check [A](https://a.com)")
    write(f2, "No links here")

    changed, cnt = convert_file(f1)
    assert changed and cnt == 1
    assert "A: https://a.com" in f1.read_text()

    files_changed, total_converted = convert_many([f1, f2])
    assert files_changed == 0
    assert total_converted == 0
