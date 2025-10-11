# tests/test_replace_emojis_text.py
from scripts.replace_emojis import replace_emojis_in_text


def test_replace_basic():
    mapping = {"🔥": "+++", "📈": "↑"}
    text = "growth 📈 and energy 🔥🔥"
    out, n = replace_emojis_in_text(text, mapping)
    assert out == "growth ↑ and energy ++++++"
    assert n == 3


def test_replace_handles_overlap_order():
    # If one key were a substring of another (rare with emojis), length-desc prevents partial
    mapping = {"AB": "X", "A": "Y"}  # simulate multi-codepoint “emoji”
    text = "AB A AB"
    out, n = replace_emojis_in_text(text, mapping)
    assert out == "X Y X"
    assert n == 3


def test_replace_no_change_on_empty():
    out, n = replace_emojis_in_text("", {"🧠": "★"})
    assert out == ""
    assert n == 0
