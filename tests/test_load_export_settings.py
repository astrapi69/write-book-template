# tests/test_load_export_settings.py
"""Tests for load_export_settings() and get_section_order_from_settings()."""
import json
import pytest

from scripts.full_export_book import (
    load_export_settings,
    get_section_order_from_settings,
)


@pytest.fixture()
def settings_file(tmp_path):
    """Create a temporary export-settings.json and return its path."""
    data = {
        "formats": {
            "markdown": "gfm",
            "pdf": "pdf",
            "epub": "epub",
        },
        "toc_depth": 3,
        "epub_skip_toc_files": ["front-matter/toc.md"],
        "section_order": {
            "default": ["chapters", "back-matter/epilogue.md"],
            "ebook": None,
            "paperback": ["front-matter/toc-print.md", "chapters"],
            "hardcover": None,
            "audiobook": ["front-matter/preface.md", "chapters"],
        },
    }
    path = tmp_path / "export-settings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# --- load_export_settings ---------------------------------------------------


def test_load_export_settings_reads_json(settings_file):
    result = load_export_settings(settings_file)
    assert result["toc_depth"] == 3
    assert "markdown" in result["formats"]


def test_load_export_settings_missing_file_returns_empty(tmp_path):
    result = load_export_settings(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_export_settings_returns_formats(settings_file):
    result = load_export_settings(settings_file)
    assert result["formats"] == {"markdown": "gfm", "pdf": "pdf", "epub": "epub"}


def test_load_export_settings_returns_epub_skip(settings_file):
    result = load_export_settings(settings_file)
    assert result["epub_skip_toc_files"] == ["front-matter/toc.md"]


# --- get_section_order_from_settings -----------------------------------------


def test_get_section_order_default(settings_file):
    settings = load_export_settings(settings_file)
    order = get_section_order_from_settings(settings, "default")
    assert order == ["chapters", "back-matter/epilogue.md"]


def test_get_section_order_ebook_falls_back_to_default(settings_file):
    """ebook is null in the test fixture -> should fall back to 'default' key."""
    settings = load_export_settings(settings_file)
    order = get_section_order_from_settings(settings, "ebook")
    assert order == ["chapters", "back-matter/epilogue.md"]


def test_get_section_order_paperback_explicit(settings_file):
    settings = load_export_settings(settings_file)
    order = get_section_order_from_settings(settings, "paperback")
    assert order == ["front-matter/toc-print.md", "chapters"]


def test_get_section_order_hardcover_falls_back_to_paperback(settings_file):
    """hardcover is null -> should fall back to 'paperback' key."""
    settings = load_export_settings(settings_file)
    order = get_section_order_from_settings(settings, "hardcover")
    assert order == ["front-matter/toc-print.md", "chapters"]


def test_get_section_order_audiobook_explicit(settings_file):
    settings = load_export_settings(settings_file)
    order = get_section_order_from_settings(settings, "audiobook")
    assert order == ["front-matter/preface.md", "chapters"]


def test_get_section_order_unknown_type_returns_none(settings_file):
    """An unknown book type with no key should return None (caller uses built-in)."""
    settings = load_export_settings(settings_file)
    order = get_section_order_from_settings(settings, "comic")
    assert order is None


def test_get_section_order_empty_settings_returns_none():
    """Empty settings dict should return None."""
    order = get_section_order_from_settings({}, "ebook")
    assert order is None


def test_get_section_order_no_section_order_key():
    """Settings with other keys but no section_order should return None."""
    settings = {"formats": {"pdf": "pdf"}, "toc_depth": 2}
    order = get_section_order_from_settings(settings, "ebook")
    assert order is None
