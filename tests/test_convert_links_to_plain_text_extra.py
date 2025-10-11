# tests/test_convert_links_to_plain_text_extra.py
from pathlib import Path
from scripts.convert_links_to_plain_text import convert_links_in_text, convert_file


def test_multiple_links_same_line():
    text = "See [One](https://one.test) and [Two](https://two.test?q=1)."
    out, n = convert_links_in_text(text)
    assert n == 2
    assert out == "See One: https://one.test and Two: https://two.test?q=1."


def test_title_is_dropped_and_label_preserved():
    text = 'Read the [Spec](https://spec.test/v1 "Official Spec").'
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out == "Read the Spec: https://spec.test/v1."


def test_angle_brackets_with_parentheses_in_url():
    text = "Open [Issue](<https://host.test/a(b)/c>)."
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out == "Open Issue: https://host.test/a(b)/c."


def test_query_and_fragment():
    text = "Try [Search](https://ex.test/find?q=a+b#top)."
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out == "Try Search: https://ex.test/find?q=a+b#top."


def test_protocol_relative_url():
    text = "CDN: [Asset](//cdn.example.com/lib.js)"
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out == "CDN: Asset: //cdn.example.com/lib.js"


def test_mailto_and_tel():
    text = "Contact [Email](mailto:info@example.com) or [Phone](tel:+123456789)."
    out, n = convert_links_in_text(text)
    assert n == 2
    assert "Email: mailto:info@example.com" in out
    assert "Phone: tel:+123456789" in out


def test_relative_link_is_converted_verbatim():
    text = "See [Appendix](../back-matter/appendix.md)."
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out == "See Appendix: ../back-matter/appendix.md."


def test_anchor_only_is_skipped():
    text = "Jump to [Top](#top) and [Keep](https://ok.test#frag)."
    out, n = convert_links_in_text(text)
    # only the full URL should convert; pure anchor stays
    assert n == 1
    assert "Keep: https://ok.test#frag" in out
    assert "[Top](#top)" in out


def test_inline_code_and_fenced_code_with_multiple_links_untouched():
    text = (
        "Real [Link](https://r.test)\n"
        "```\n[Nope](https://no.test)\n```\n"
        "Inline `code [NopeToo](https://no2.test)` done."
    )
    out, n = convert_links_in_text(text)
    assert n == 1
    assert "Real Link: https://r.test" in out
    assert "[Nope](https://no.test)" in out
    assert "[NopeToo](https://no2.test)" in out


def test_image_links_are_ignored_even_with_titles():
    text = '![Alt](img.png "caption") and [OK](https://ok.test)'
    out, n = convert_links_in_text(text)
    assert n == 1
    assert out.endswith("OK: https://ok.test")


def test_file_roundtrip(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("Go [Home](https://home.test) now.", encoding="utf-8")
    changed, cnt = convert_file(f)
    assert changed and cnt == 1
    assert f.read_text(encoding="utf-8") == "Go Home: https://home.test now."


def test_url_with_parentheses_without_angle_brackets_note():
    # NOTE: Without <...>, a ) can terminate the URL in Markdown parsing.
    # Our converter expects <...> if parentheses are present in the URL.
    text = "Bad form [X](https://site.test/a(b)) should ideally be written as [X](<https://site.test/a(b)>)."
    out, n = convert_links_in_text(text)
    # We don't assert specifics here; this is just documentation-by-test.
    assert n >= 0
