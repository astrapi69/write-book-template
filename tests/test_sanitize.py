# tests/test_sanitize.py
from __future__ import annotations
from pathlib import Path
import pytest

from scripts.sanitize import sanitize_markdown, process_file, main


def test_sanitize_replaces_invisibles_and_maps_spaces():
    dirty = (
        "A\u200bB"
        " C\u00adD"
        " E\u00a0F"
        " G\u202fH"
        " I\u200eJ\u200fK"
        " L\u2028M\u2029N"
    )
    cleaned = sanitize_markdown(dirty)

    assert "\u200b" not in cleaned
    assert "\u00ad" not in cleaned
    assert "\u200e" not in cleaned
    assert "\u200f" not in cleaned

    assert "E F" in cleaned
    assert "G H" in cleaned

    assert "L\nM\nN" in cleaned


def test_sanitize_removes_bom_and_controls():
    dirty = "\ufeffTitle\tOK\nBad:\x00\x01\x02\x7f End"
    cleaned = sanitize_markdown(dirty)
    assert "\ufeff" not in cleaned
    assert all(c not in cleaned for c in ["\x00", "\x01", "\x02", "\x7f"])
    assert "\t" in cleaned
    assert "\n" in cleaned


def test_newline_normalization_and_trailing_newline():
    dirty = "Line1\r\nLine2\rLine3"
    cleaned = sanitize_markdown(dirty)
    assert cleaned == "Line1\nLine2\nLine3\n"


def test_process_file_writes_and_backup(tmp_path: Path):
    p = tmp_path / "doc.md"
    p.write_text("A\u200bB", encoding="utf-8")
    changed = process_file(p, dry_run=False, backup=True)
    assert changed is True
    assert p.read_text(encoding="utf-8") == "AB\n"
    assert (tmp_path / "doc.md.bak").exists()
    assert (tmp_path / "doc.md.bak").read_text(encoding="utf-8") == "A\u200bB"


def test_process_file_no_change_no_backup(tmp_path: Path):
    p = tmp_path / "clean.md"
    p.write_text("Already clean\n", encoding="utf-8")
    changed = process_file(p, dry_run=False, backup=True)
    assert changed is False
    assert not (tmp_path / "clean.md.bak").exists()


def test_main_dry_run_and_excludes(tmp_path: Path, capsys: pytest.CaptureFixture):
    root = tmp_path / "manuscript"
    (root / "sub").mkdir(parents=True)
    inc = root / "keep.md"
    exc = root / "sub" / "skip.md"

    inc.write_text("Hello\u00a0World", encoding="utf-8")
    exc.write_text("X\u200bY", encoding="utf-8")

    main(
        [
            "--root",
            str(root),
            "--include",
            "**/*.md",
            "--exclude",
            "sub/*.md",
            "--dry-run",
        ]
    )

    out = capsys.readouterr().out
    assert "WOULD clean" in out and "keep.md" in out
    assert "skip.md" not in out
    assert inc.read_text(encoding="utf-8") == "Hello\u00a0World"


def test_main_actual_write(tmp_path: Path, capsys: pytest.CaptureFixture):
    root = tmp_path / "manuscript"
    root.mkdir()
    f = root / "t.md"
    f.write_text("C\u00a0D", encoding="utf-8")

    main(["--root", str(root)])

    out = capsys.readouterr().out
    assert "Cleaned" in out and "t.md" in out
    assert f.read_text(encoding="utf-8") == "C D\n"
