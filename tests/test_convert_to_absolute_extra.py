# tests/test_convert_to_absolute_extra.py
from pathlib import Path
import os
from scripts.convert_to_absolute import convert_file_to_absolute, convert_to_absolute


def write(p: Path, txt: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")


def test_relative_with_dot_and_dotdot(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters" / "sub"
    img = base / "assets" / "imgs" / "a.png"
    write(img, "x")

    md = ch / "doc.md"
    rel1 = os.path.relpath(img, start=md.parent)  # e.g. ../../assets/imgs/a.png
    rel2 = "./" + os.path.relpath(
        img, start=md.parent
    )  # ./../../assets/imgs/a.png (still valid)
    write(md, f"![one]({rel1}) and ![two]({rel2})")

    changed, cnt = convert_file_to_absolute(md)
    assert changed and cnt == 2
    out = md.read_text(encoding="utf-8")
    assert str(img.resolve()) in out
    assert out.count("![") == 2


def test_protocol_and_data_urls_are_ignored(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    md = ch / "urls.md"
    text = (
        "![http](https://example.com/a.png) "
        "![proto-rel](//cdn.example.com/a.png) "
        "![mailto](mailto:info@example.com) "
        "![data](data:image/png;base64,iVBORw0KGgo...)"
    )
    write(md, text)

    changed, cnt = convert_file_to_absolute(md)
    # nothing to convert; all are "url-like"
    assert not changed and cnt == 0
    assert md.read_text(encoding="utf-8") == text


def test_multiple_images_same_line_mixed(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img1 = base / "assets" / "a.png"
    img2 = base / "assets" / "b.png"
    write(img1, "x")
    write(img2, "x")

    md = ch / "multi.md"
    rel1 = os.path.relpath(img1, start=md.parent)
    rel2 = os.path.relpath(img2, start=md.parent)
    text = f"![a]({rel1})![b]({rel2}) ![skip](https://host/p.png)"
    write(md, text)

    changed, cnt = convert_file_to_absolute(md)
    assert changed and cnt == 2
    out = md.read_text(encoding="utf-8")
    assert str(img1.resolve()) in out and str(img2.resolve()) in out
    assert "https://host/p.png" in out


def test_single_quoted_title_is_preserved(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "c.png"
    write(img, "x")

    md = ch / "title_single_quote.md"
    rel = os.path.relpath(img, start=md.parent)
    write(md, f"![sq](<{rel}> 'Cover')")

    changed, cnt = convert_file_to_absolute(md)
    assert changed and cnt == 1
    out = md.read_text(encoding="utf-8")
    # title stays inside parens; path becomes absolute
    assert f"![sq]({img.resolve()} 'Cover')" in out


def test_mixed_convertible_and_nonconvertible(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "d.png"
    write(img, "x")

    md = ch / "mix.md"
    rel = os.path.relpath(img, start=md.parent)
    text = (
        f"![ok]({rel})\n"
        f"![missing](images/none.png)\n"
        f"![url](https://ex.com/x.png)\n"
        f"`inline ![nope]({rel})`\n"
        f"```\nblock ![nope2]({rel})\n```\n"
    )
    write(md, text)

    changed, cnt = convert_file_to_absolute(md)
    assert changed and cnt == 1
    out = md.read_text(encoding="utf-8")
    assert f"![ok]({img.resolve()})" in out
    assert "![missing](images/none.png)" in out
    assert "![url](https://ex.com/x.png)" in out
    assert "`inline ![nope]" in out
    assert "block ![nope2]" in out


def test_walk_three_default_dirs_with_mixed_content(tmp_path: Path):
    base = tmp_path
    ch = base / "manuscript" / "chapters"
    fm = base / "manuscript" / "front-matter"
    bm = base / "manuscript" / "back-matter"
    img = base / "assets" / "e.png"
    write(img, "x")

    md1 = ch / "a.md"
    md2 = fm / "b.md"
    md3 = bm / "c.md"
    rel1 = os.path.relpath(img, start=md1.parent)
    rel2 = os.path.relpath(img, start=md2.parent)
    write(md1, f"![a]({rel1})")
    write(
        md2, f'![b]({rel2}) "trailer text"'
    )  # trailing text after tag to ensure we match minimally
    write(md3, "No images here")

    files_changed, converted = convert_to_absolute([ch, fm, bm])
    assert files_changed == 2 and converted == 2
