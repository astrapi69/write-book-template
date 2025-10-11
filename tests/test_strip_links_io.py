# tests/test_strip_links_io.py
from pathlib import Path
from scripts.strip_links import process_file


def test_process_overwrite(tmp_path: Path):
    f = tmp_path / "t.md"
    f.write_text("A [b](c) D", encoding="utf-8")
    src, n, dest = process_file(f, overwrite=True, suffix="-nolinks.md")
    assert n == 1
    assert dest == f
    assert f.read_text(encoding="utf-8") == "A b D"


def test_process_copy_only_when_changed(tmp_path: Path):
    f = tmp_path / "t.md"
    f.write_text("no links here", encoding="utf-8")
    src, n, dest = process_file(f, overwrite=False, suffix="-nolinks.md")
    assert n == 0
    assert dest is None
    assert not (tmp_path / "t-nolinks.md").exists()


def test_process_copy_when_changed(tmp_path: Path):
    f = tmp_path / "t.md"
    f.write_text("A [b](c)", encoding="utf-8")
    src, n, dest = process_file(f, overwrite=False, suffix="-nolinks.md")
    assert n == 1
    assert dest == tmp_path / "t-nolinks.md"
    assert dest.read_text(encoding="utf-8") == "A b"
