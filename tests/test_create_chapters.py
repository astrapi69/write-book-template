# tests/test_create_chapters.py
from __future__ import annotations

import pytest

from scripts.create_chapters import create_chapter_files, DEFAULT_PATTERN


def test_creates_files_in_default_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    created = create_chapter_files(
        project_dir=None, total=3, start=1, name_pattern=DEFAULT_PATTERN
    )
    chapter_dir = tmp_path / "manuscript" / "chapters"
    assert chapter_dir.is_dir()
    assert [p.name for p in created] == [
        "01-chapter.md",
        "02-chapter.md",
        "03-chapter.md",
    ]


def test_respects_project_dir_and_custom_pattern(tmp_path):
    project_root = tmp_path / "myproj"
    created = create_chapter_files(
        project_dir=project_root, total=2, start=4, name_pattern="{num:02d}-scene.md"
    )
    chapter_dir = project_root / "manuscript" / "chapters"
    assert chapter_dir.is_dir()
    assert [p.name for p in created] == ["04-scene.md", "05-scene.md"]


def test_autostart_after_existing_with_custom_pattern(tmp_path):
    project_root = tmp_path / "proj"
    chapter_dir = project_root / "manuscript" / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    # Seed files that match the custom pattern
    (chapter_dir / "01-scene.md").touch()
    (chapter_dir / "02-scene.md").touch()

    created = create_chapter_files(
        project_dir=project_root, total=2, start=None, name_pattern="{num:02d}-scene.md"
    )
    assert [p.name for p in created] == ["03-scene.md", "04-scene.md"]


def test_autostart_ignores_nonmatching_files(tmp_path):
    project_root = tmp_path / "proj2"
    chapter_dir = project_root / "manuscript" / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    # Non-matching filenames shouldn't affect detection
    (chapter_dir / "99-chapter.md").touch()
    (chapter_dir / "README.md").touch()

    created = create_chapter_files(
        project_dir=project_root, total=2, start=None, name_pattern="{num:02d}-scene.md"
    )
    # No existing scenes -> starts at 1
    assert [p.name for p in created] == ["01-scene.md", "02-scene.md"]


def test_dry_run_with_pattern_creates_nothing(tmp_path):
    project_root = tmp_path / "dry"
    planned = create_chapter_files(
        project_dir=project_root,
        total=2,
        start=1,
        dry_run=True,
        name_pattern="{num:03d}_part.md",
    )
    chapter_dir = project_root / "manuscript" / "chapters"
    assert not chapter_dir.exists()
    assert [p.name for p in planned] == ["001_part.md", "002_part.md"]


def test_invalid_total_raises(tmp_path):
    with pytest.raises(ValueError):
        create_chapter_files(
            project_dir=tmp_path, total=0, start=1, name_pattern="{num}-x.md"
        )


def test_invalid_start_raises(tmp_path):
    with pytest.raises(ValueError):
        create_chapter_files(
            project_dir=tmp_path, total=1, start=0, name_pattern="{num}-x.md"
        )


def test_missing_num_placeholder_raises(tmp_path):
    with pytest.raises(ValueError):
        create_chapter_files(
            project_dir=tmp_path, total=1, start=1, name_pattern="chapter.md"
        )
