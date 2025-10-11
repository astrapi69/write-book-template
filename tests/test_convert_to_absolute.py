# tests/test_convert_to_absolute.py
from pathlib import Path
import os
from scripts.convert_to_absolute import convert_to_absolute, convert_file_to_absolute


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_converts_relative_image_to_absolute(tmp_path: Path):
    base = tmp_path
    chapters = base / "manuscript" / "chapters"
    img = base / "assets" / "figs" / "a.png"
    write(img, "x")

    md = chapters / "01.md"
    rel = os.path.relpath(img, start=md.parent)
    write(md, f"Before\n![alt]({rel})\nAfter\n")

    changed, count = convert_file_to_absolute(md)
    assert changed and count == 1
    out = md.read_text(encoding="utf-8")
    assert f"![alt]({img.resolve()})" in out


def test_keeps_already_absolute_and_skips_missing(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img_abs = base / "assets" / "b.png"
    write(img_abs, "x")

    md = ch / "02.md"
    # one absolute (should remain), one missing (should remain unchanged)
    write(md, f"![abs]({img_abs}) and ![missing](images/notthere.png)")

    changed, count = convert_file_to_absolute(md)
    # nothing to convert: first is absolute, second doesn't exist
    assert (changed is False) and (count == 0)
    assert md.read_text(encoding="utf-8").count("![") == 2


def test_preserves_title_and_handles_angle_brackets(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "weird (name).png"
    write(img, "x")

    md = ch / "03.md"
    rel = os.path.relpath(img, start=md.parent)
    # with a title and with angle-brackets
    write(md, f'![titled](<{rel}> "Cover")\n![angled](<{rel}>)')

    changed, count = convert_file_to_absolute(md)
    assert changed and count == 2
    out = md.read_text(encoding="utf-8")
    assert f'![titled]({img.resolve()} "Cover")' in out
    assert f"![angled]({img.resolve()})" in out


def test_skips_inside_code_blocks_and_inline_code(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "c.png"
    write(img, "x")

    md = ch / "04.md"
    rel = os.path.relpath(img, start=md.parent)
    text = (
        "Visible ![ok](" + rel + ")\n"
        "```\ncode ![nope](" + rel + ")\n```\n"
        "Inline `![nope2](" + rel + ")` end."
    )
    write(md, text)

    changed, count = convert_file_to_absolute(md)
    assert changed and count == 1
    out = md.read_text(encoding="utf-8")
    # Only the visible one converted; code-block and inline stayed as-is
    assert f"![ok]({img.resolve()})" in out
    assert "code ![nope](" in out
    assert "`![nope2](" in out


def test_directory_walk_multiple_dirs(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    fm = base / "manuscript" / "front-matter"
    img1 = base / "assets" / "d.png"
    img2 = base / "assets" / "e.png"
    write(img1, "x")
    write(img2, "x")

    md1 = ch / "a.md"
    md2 = fm / "b.md"
    rel1 = os.path.relpath(img1, start=md1.parent)
    rel2 = os.path.relpath(img2, start=md2.parent)
    write(md1, f"![a]({rel1})")
    write(md2, f"![b]({rel2})")

    files_changed, converted = convert_to_absolute([ch, fm])
    assert files_changed == 2
    assert converted == 2


def test_no_write_when_no_change(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "x.png"
    write(img, "x")
    md = ch / "z.md"
    write(md, f"![abs]({img.resolve()})")

    changed, count = convert_file_to_absolute(md)
    assert changed is False and count == 0
    assert md.read_text(encoding="utf-8").startswith("![abs](")
