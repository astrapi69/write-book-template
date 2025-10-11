# tests/test_generate_audiobook_cleaner_use_cases.py
import textwrap
from scripts.generate_audiobook import clean_markdown_for_tts


def test_mixed_markdown_html_content_is_readable():
    src = textwrap.dedent(
        """
    <!-- intro -->
    # Chapter 01: Arrival

    <figure class="hero">
      <img src="assets/hero.png" alt="Hero"/>
      <figcaption><em>Caption</em></figcaption>
    </figure>

    Welcome to **New Eden** — see [docs](https://example.com/docs).
    Table below (should be removed):
    | a | b |
    |---|---|
    | 1 | 2 |

    Code:
    ```
    print("nope")
    ```

    Inline `var = 42` is ok.
    """
    )
    out = clean_markdown_for_tts(src)
    # Essentials preserved
    assert "Chapter 01: Arrival" in out
    assert "Welcome to New Eden — see docs." in out
    assert "var = 42" in out
    # Noise gone
    assert "figure" not in out.lower()
    assert "hero.png" not in out
    assert "|" not in out
    assert "print(" not in out


def test_multilingual_and_entities():
    src = "Hola&nbsp;niña &amp; niño — déjà vu &uuml;ber alles"
    out = clean_markdown_for_tts(src)
    # NBSP normalized to plain space; &amp; unescaped; ü from &uuml; handled
    assert "Hola niña & niño — déjà vu über alles" in out


def test_reference_link_spam_removed():
    src = textwrap.dedent(
        """
    Read about the [last spark][ls] and [universal fire][] now.
    [ls]: https://a.example
    [universal fire]: https://b.example
    """
    )
    out = clean_markdown_for_tts(src)
    assert "last spark" in out and "universal fire" in out
    assert "example" not in out
    # no remaining definition lines
    assert "[" not in "\n".join(
        line for line in out.splitlines() if line.strip().startswith("[")
    )


def test_heading_only_chapter_still_produces_text():
    src = "# Only a Title"
    out = clean_markdown_for_tts(src)
    assert out == "Only a Title"
