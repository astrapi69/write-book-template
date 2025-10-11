# tests/test_generate_audiobook_clean_markdown_for_tts.py
import textwrap
from scripts.generate_audiobook import clean_markdown_for_tts


def norm(s: str) -> str:
    return "\n".join(line.rstrip() for line in s.strip().splitlines())


def test_removes_full_figure_block():
    src = textwrap.dedent(
        """
    <p>Intro before.</p>
    <figure class="img">
      <img src="assets/village-without-money.png" alt="_..._" />
      <figcaption><em>_..._</em></figcaption>
    </figure>
    <p>After figure.</p>
    """
    )
    out = clean_markdown_for_tts(src)
    assert "village-without-money.png" not in out
    assert "figcaption" not in out.lower()
    assert "After figure." in out
    assert "Intro before." in out


def test_removes_markdown_images_and_keeps_link_text():
    src = "Text ![alt](img.png) and [click here](https://example.com  )."
    out = clean_markdown_for_tts(src)
    assert "img.png" not in out
    assert "click here" in out
    assert "(" not in out  # no URL residue


def test_reference_links_and_definitions_removed():
    src = textwrap.dedent(
        """
    Some [text][id] and [more][] around.

    [id]: https://example.com
    [more]: https://example.org
    """
    )
    out = clean_markdown_for_tts(src)
    out_n = norm(out)
    assert "text" in out_n and "more" in out_n
    assert "example.com" not in out_n and "example.org" not in out_n
    assert not any(line.strip().startswith("[") for line in out_n.splitlines())


def test_code_blocks_and_inline_code_removed():
    src = textwrap.dedent(
        """
    Here is code:
    ```
    print("hello")
    ```
    Inline `x = 1` end.
    """
    )
    out = clean_markdown_for_tts(src)
    assert "print(" not in out
    assert "x = 1" in out  # inline code content preserved


def test_headings_bold_italics_tables_removed():
    src = textwrap.dedent(
        """
    # Title
    This is **bold** and _italic_ and __strong__.

    | a | b |
    |---|---|
    | 1 | 2 |
    """
    )
    out = clean_markdown_for_tts(src)
    assert "Title" in out
    assert "**" not in out and "_" not in out
    assert "|" not in out


def test_html_comments_removed_and_excess_newlines_collapsed():
    src = "A<!-- hidden -->\n\n\nB"
    out = clean_markdown_for_tts(src)
    assert "<!--" not in out
    assert "\n\n\n" not in out


def test_yaml_front_matter_removed_and_entities_unescaped():
    src = textwrap.dedent(
        """\
    ---
    title: Test
    author: You &amp; Me
    ---
    Hello&nbsp;World &amp; Co.
    """
    )
    out = clean_markdown_for_tts(src)
    assert "title:" not in out and "author:" not in out
    assert "Hello World & Co." in out
