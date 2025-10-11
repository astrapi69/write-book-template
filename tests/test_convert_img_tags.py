# tests/test_convert_img_tags.py
from pathlib import Path
import os
import re

from scripts.convert_img_tags import convert_markdown_tree


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_to_absolute_converts_relative_and_leaves_abs(tmp_path: Path):
    base = tmp_path
    # Project structure
    chapters = base / "manuscript" / "chapters"
    assets = base / "assets" / "figures"
    img = assets / "scene" / "pic.png"
    write(img, "binary")  # just to create the file

    # Markdown with mixed <img> tags (single and double quotes, extra attrs)
    md = chapters / "01.md"
    rel_path = os.path.relpath(img, start=md.parent)
    content = (
        f"Before\n"
        f'<img src="{rel_path}" alt="rel" class="c"/>\n'
        f'<img alt="already-abs" src="{img}" width="100">\n'
        f"<img src='{rel_path}' alt='single-quoted'>\n"
        f"After\n"
    )
    write(md, content)

    changed, converted = convert_markdown_tree(base, to_absolute=True)
    assert changed == 1
    assert converted == 2  # only the two relative ones

    new_text = md.read_text(encoding="utf-8")
    # Both relative srcs should now be absolute
    abs_pattern = re.compile(r'<img[^>]*\bsrc="([^"]+)"')
    srcs = abs_pattern.findall(new_text)
    assert any(str(img) in s for s in srcs)
    assert new_text.count(str(img)) == 3  # one was already absolute, plus two converted


def test_to_relative_only_under_assets(tmp_path: Path):
    base = tmp_path
    chapters = base / "manuscript" / "chapters"
    assets = base / "assets" / "figures"
    other_abs_dir = base / "outside"
    img_assets = assets / "hero.png"
    img_outside = other_abs_dir / "not-in-assets.png"
    write(img_assets, "x")
    write(img_outside, "x")

    md = chapters / "02.md"
    text = (
        f'<img src="{img_assets}" alt="ok">\n' f'<img src="{img_outside}" alt="skip">\n'
    )
    write(md, text)

    changed, converted = convert_markdown_tree(
        base, to_absolute=False, assets_dir=base / "assets"
    )
    assert changed == 1
    assert converted == 1

    new_text = md.read_text(encoding="utf-8")
    first_line = new_text.splitlines()[0]
    # The assets image becomes relative (not absolute), the outside one stays absolute
    assert 'alt="ok"' in first_line
    assert not first_line.startswith("/") and not first_line.startswith(
        str(base)
    )  # relative, not absolute
    assert str(img_outside) in new_text  # untouched


def test_no_write_when_no_change(tmp_path: Path):
    base = tmp_path
    chapters = base / "manuscript" / "chapters"
    img = base / "assets" / "pic.png"
    write(img, "x")
    md = chapters / "03.md"
    # Already absolute inside assets; converting to absolute should not change
    text = f'<img src="{img}" alt="abs"/>\n'
    write(md, text)

    changed, converted = convert_markdown_tree(base, to_absolute=True)
    assert changed == 0
    assert converted == 0
    assert md.read_text(encoding="utf-8") == text


def test_preserves_other_attributes_and_normalizes_order(tmp_path: Path):
    base = tmp_path
    chapters = base / "manuscript" / "chapters"
    img = base / "assets" / "a.png"
    write(img, "x")
    md = chapters / "04.md"
    rel = os.path.relpath(img, start=md.parent)
    # alt before src, extra attributes and irregular spacing
    write(md, f'<img   alt="x"   data-id="123"   src="{rel}"   class="y">')

    convert_markdown_tree(base, to_absolute=True)

    t = md.read_text(encoding="utf-8")
    # Normalized to src then alt then others (alpha order)
    assert t.startswith("<img ")
    assert 'src="' in t and 'alt="' in t
    src_pos = t.index('src="')
    alt_pos = t.index('alt="')
    assert src_pos < alt_pos
    # Other attributes present
    assert 'class="y"' in t and 'data-id="123"' in t
