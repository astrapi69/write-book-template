# tests/test_replace_emojis_io.py
from pathlib import Path
from scripts.replace_emojis import process_file


def test_process_file_overwrite(tmp_path: Path):
    src = tmp_path / "a.md"
    src.write_text("hi 🔥", encoding="utf-8")
    mapping = {"🔥": "+++"}
    s, n, dest = process_file(
        src, overwrite=True, suffix="-final.md", mapping=mapping, encoding="utf-8"
    )
    assert s == src
    assert n == 1
    assert dest == src
    assert src.read_text(encoding="utf-8") == "hi +++"


def test_process_file_copy_only_if_changed(tmp_path: Path):
    src = tmp_path / "a.md"
    src.write_text("no emojis here", encoding="utf-8")
    mapping = {"🔥": "+++"}
    s, n, dest = process_file(
        src, overwrite=False, suffix="-final.md", mapping=mapping, encoding="utf-8"
    )
    assert n == 0
    assert dest is None
    assert (tmp_path / "a-final.md").exists() is False
