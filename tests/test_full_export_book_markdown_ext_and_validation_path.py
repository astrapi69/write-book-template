# tests/test_full_export_book_markdown_ext_and_validation_path.py
import sys
from pathlib import Path
import importlib


def test_resolve_ext_for_markdown_and_others(monkeypatch):
    """
    Verifies:
    - markdown default ext is 'md'
    - markdown custom ext is respected
    - other formats use FORMATS mapping as-is
    """
    # Make repo root importable (assuming tests/ is at repo root)
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    # Prevent chdir side-effects during import
    import os

    monkeypatch.setattr(os, "chdir", lambda _p: None)

    feb = importlib.import_module("scripts.full_export_book")

    # Sanity: module must expose FORMATS and resolve_ext
    assert hasattr(feb, "FORMATS"), "FORMATS not found in module"
    assert hasattr(feb, "resolve_ext"), "resolve_ext not found in module"

    # markdown defaults to 'md'
    assert feb.resolve_ext("markdown", None) == "md"

    # custom ext for markdown
    assert feb.resolve_ext("markdown", "markdown") == "markdown"
    assert feb.resolve_ext("markdown", "mdown") == "mdown"

    # others come from mapping
    assert feb.resolve_ext("pdf", None) == feb.FORMATS["pdf"]  # usually "pdf"
    assert feb.resolve_ext("epub", None) == feb.FORMATS["epub"]
    assert feb.resolve_ext("docx", None) == feb.FORMATS["docx"]


def test_validator_path_uses_resolved_ext(monkeypatch, tmp_path):
    """
    Simulate how the exporter computes output paths for validation.
    Ensures that markdown uses the resolved extension (default or custom).
    """
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    import os

    monkeypatch.setattr(os, "chdir", lambda _p: None)
    feb = importlib.import_module("scripts.full_export_book")

    OUTPUT_FILE = "mybook-ebook"
    OUTPUT_DIR = tmp_path / "output"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def out_path(fmt, custom=None):
        ext = feb.resolve_ext(fmt, custom if fmt == "markdown" else None)
        return OUTPUT_DIR / f"{OUTPUT_FILE}.{ext}"

    # default markdown -> .md
    assert out_path("markdown").name == "mybook-ebook.md"

    # custom markdown extension -> respected
    assert out_path("markdown", custom="gfm").name == "mybook-ebook.gfm"
    assert out_path("markdown", custom="markdown").name == "mybook-ebook.markdown"

    # other formats unchanged
    assert out_path("pdf").name == "mybook-ebook.pdf"
    assert out_path("epub").name == "mybook-ebook.epub"
    assert out_path("docx").name == "mybook-ebook.docx"


def test_resolve_ext_and_paths(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    # neutralize chdir side-effects in module import
    import os

    monkeypatch.setattr(os, "chdir", lambda _p: None)

    feb = importlib.import_module("scripts.full_export_book")
    assert hasattr(feb, "resolve_ext")

    # default markdown -> .md
    assert feb.resolve_ext("markdown", None) == "md"
    # custom markdown extension respected
    assert feb.resolve_ext("markdown", "gfm") == "gfm"

    # others via mapping
    assert feb.resolve_ext("pdf", None) == feb.FORMATS["pdf"]
    assert feb.resolve_ext("epub", None) == feb.FORMATS["epub"]
    assert feb.resolve_ext("docx", None) == feb.FORMATS["docx"]

    # simulate how output path is built for validation
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = "mybook-ebook"

    def out(fmt, custom=None):
        ext = feb.resolve_ext(fmt, custom if fmt == "markdown" else None)
        return (output_dir / f"{output_file}.{ext}").name

    assert out("markdown") == "mybook-ebook.md"
    assert out("markdown", "markdown") == "mybook-ebook.markdown"
    assert out("pdf") == "mybook-ebook.pdf"
    assert out("epub") == "mybook-ebook.epub"
    assert out("docx") == "mybook-ebook.docx"
