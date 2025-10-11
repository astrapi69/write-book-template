# tests/test_pandoc_batch_patch_markdown_text.py
from scripts.pandoc_batch import patch_markdown_text


def test_patch_strips_bom_and_normalizes_newlines():
    raw = "\ufeffLine1\r\n---\r\nLine2"
    patched, n = patch_markdown_text(raw)
    assert "\ufeff" not in patched
    assert "\r" not in patched
    # HR should be followed by a blank line
    assert "\n---\n\n" in patched
    assert n >= 1


def test_patch_no_change_on_clean_text():
    raw = "Hello\n\n---\n\nWorld\n"
    patched, n = patch_markdown_text(raw)
    assert patched == raw
    assert n == 0
