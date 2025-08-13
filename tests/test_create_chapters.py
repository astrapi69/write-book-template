# tests/test_create_chapters.py
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Import from the scripts package path. Adjust if your test runner needs PYTHONPATH tweak.
from scripts.create_chapters import create_chapter_files, main as create_chapters_main


def test_creates_files_in_default_dir(tmp_path, monkeypatch):
    # Run in a temp project root
    monkeypatch.chdir(tmp_path)

    created = create_chapter_files(project_dir=None, total=3, start=1)
    assert len(created) == 3

    chapter_dir = tmp_path / "manuscript" / "chapters"
    assert chapter_dir.is_dir()

    expected = [chapter_dir / f"{i:02d}-chapter.md" for i in (1, 2, 3)]
    for p in expected:
        assert p.exists()


def test_respects_project_dir(tmp_path):
    project_root = tmp_path / "myproj"
    created = create_chapter_files(project_dir=project_root, total=2, start=4)
    chapter_dir = project_root / "manuscript" / "chapters"
    assert chapter_dir.is_dir()

    assert (chapter_dir / "04-chapter.md").exists()
    assert (chapter_dir / "05-chapter.md").exists()
    assert len(created) == 2


def test_autostart_after_existing(tmp_path):
    project_root = tmp_path / "proj"
    chapter_dir = project_root / "manuscript" / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    # Pre-create chapters 01 and 02
    (chapter_dir / "01-chapter.md").touch()
    (chapter_dir / "02-chapter.md").touch()

    # No start provided -> should continue with 03, 04
    created = create_chapter_files(project_dir=project_root, total=2, start=None)
    paths = [p.name for p in created]
    assert "03-chapter.md" in paths
    assert "04-chapter.md" in paths


def test_start_param_overrides_autodetection(tmp_path):
    project_root = tmp_path / "x"
    # Even if directory is empty, starting at 5 should create 05..07
    created = create_chapter_files(project_dir=project_root, total=3, start=5)
    names = [p.name for p in created]
    assert names == ["05-chapter.md", "06-chapter.md", "07-chapter.md"]


def test_dry_run_creates_nothing(tmp_path):
    project_root = tmp_path / "dry"
    planned = create_chapter_files(project_dir=project_root, total=2, start=1, dry_run=True)
    assert len(planned) == 2

    chapter_dir = project_root / "manuscript" / "chapters"
    assert not chapter_dir.exists()  # no directories/files created


def test_invalid_total_raises(tmp_path):
    with pytest.raises(ValueError):
        create_chapter_files(project_dir=tmp_path, total=0, start=1)


def test_invalid_start_raises(tmp_path):
    with pytest.raises(ValueError):
        create_chapter_files(project_dir=tmp_path, total=1, start=0)
