# tests/test_strip_links_text.py
from scripts.strip_links import strip_links_in_text


def test_basic_link_to_text():
    src = "See the [guide](docs/guide.md) please."
    out, n = strip_links_in_text(src)
    assert out == "See the guide please."
    assert n == 1


def test_multiple_links():
    src = "[one](a) and [two](b) and [three](c)"
    out, n = strip_links_in_text(src)
    assert out == "one and two and three"
    assert n == 3


def test_does_not_touch_images():
    src = "image: ![alt text](pic.png) and [link](x)"
    out, n = strip_links_in_text(src)
    assert out == "image: ![alt text](pic.png) and link"
    assert n == 1


def test_skips_inline_code():
    src = "keep `a [b](c) d` but strip [e](f)"
    out, n = strip_links_in_text(src)
    assert out == "keep `a [b](c) d` but strip e"
    assert n == 1


def test_skips_fenced_code_blocks_triple_backticks():
    src = "top [x](y)\n\n```python\nprint('[x](y)')\n```\nend [a](b)"
    out, n = strip_links_in_text(src)
    # Only top and end should be stripped, not inside the fence
    assert out.startswith("top x")
    assert "print('[x](y)')" in out
    assert out.rstrip().endswith("end a")
    assert n == 2


def test_skips_fenced_code_blocks_tildes():
    src = "pre [m](n)\n\n~~~\n[x](y)\n~~~\npost [o](p)"
    out, n = strip_links_in_text(src)
    assert "pre m" in out and "post o" in out
    assert "[x](y)" in out  # unchanged inside ~~~
    assert n == 2
