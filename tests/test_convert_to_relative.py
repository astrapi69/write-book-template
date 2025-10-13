# tests/test_convert_to_relative.py
import importlib.util
from pathlib import Path
import textwrap
import os
import pytest


def import_ctr(module_path: Path):
    spec = importlib.util.spec_from_file_location(
        "convert_to_relative", str(module_path)
    )
    assert spec is not None, "ModuleSpec is None"
    assert spec.loader is not None, "ModuleSpec.loader is None"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def write(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


@pytest.fixture()
def temp_project(tmp_path: Path):
    project = tmp_path
    (project / "manuscript" / "chapters").mkdir(parents=True)
    (project / "manuscript" / "front-matter").mkdir(parents=True)
    (project / "manuscript" / "back-matter").mkdir(parents=True)
    (project / "assets" / "img").mkdir(parents=True)
    return project


def test_markdown_image_absolute_to_relative(temp_project, monkeypatch):
    project = temp_project

    chapter = project / "manuscript" / "chapters" / "01-intro.md"
    pic = project / "assets" / "img" / "cover (v1).png"
    write(pic, "png")
    write(
        chapter,
        textwrap.dedent(
            f"""
            # Intro
            ![Cover](<{pic.as_posix()}> "title")
            Inline: ![x]({pic.as_posix()})
            """
        ).strip(),
    )

    # Import the implementation from your repo (tests/.. = project root)
    mod = import_ctr(
        Path(__file__).resolve().parents[1] / "scripts" / "convert_to_relative.py"
    )

    # Point the module to the temp project structure
    monkeypatch.setattr(mod, "PROJECT_ROOT", project.resolve(), raising=False)
    monkeypatch.setattr(mod, "MANUSCRIPT_DIR", project / "manuscript", raising=False)
    monkeypatch.setattr(mod, "ASSETS_DIR", project / "assets", raising=False)
    monkeypatch.setattr(
        mod,
        "MD_DIRECTORIES",
        [
            project / "manuscript" / "chapters",
            project / "manuscript" / "front-matter",
            project / "manuscript" / "back-matter",
        ],
        raising=False,
    )

    converted = mod.convert_paths_in_text(chapter.read_text(encoding="utf-8"), chapter)
    rel = Path(os.path.relpath(pic, start=chapter.parent)).as_posix()

    assert f'![Cover](<{rel}> "title")' in converted
    assert f"![x]({rel})" in converted


def test_html_img_and_a_tags(temp_project, monkeypatch):
    project = temp_project
    mod = import_ctr(
        Path(__file__).resolve().parents[1] / "scripts" / "convert_to_relative.py"
    )

    chapter = project / "manuscript" / "chapters" / "p.md"
    pic = project / "assets" / "img" / "p.png"
    write(pic, "png")
    write(chapter, f'<img src="{pic.as_posix()}"> <a href="{pic.as_posix()}">link</a>')

    monkeypatch.setattr(mod, "PROJECT_ROOT", project.resolve(), raising=False)
    monkeypatch.setattr(mod, "MANUSCRIPT_DIR", project / "manuscript", raising=False)
    monkeypatch.setattr(mod, "ASSETS_DIR", project / "assets", raising=False)

    out = mod.convert_paths_in_text(chapter.read_text(), chapter)
    rel = Path(os.path.relpath(pic, start=chapter.parent)).as_posix()
    assert f'<img src="{rel}">' in out
    assert f'<a href="{rel}">' in out


def test_skip_urls_anchors_and_non_assets(temp_project, monkeypatch):
    project = temp_project
    mod = import_ctr(
        Path(__file__).resolve().parents[1] / "scripts" / "convert_to_relative.py"
    )

    chapter = project / "manuscript" / "chapters" / "p.md"
    outside = project / "notassets" / "p.png"
    write(outside, "x")

    write(
        chapter,
        textwrap.dedent(
            f"""
            [web](https://example.com)
            [anchor](#sec)
            ![outside]({outside.as_posix()})
            rel ok
            """
        ).strip(),
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project.resolve(), raising=False)
    monkeypatch.setattr(mod, "ASSETS_DIR", project / "assets", raising=False)

    out = mod.convert_paths_in_text(chapter.read_text(), chapter)
    assert out == chapter.read_text()  # unchanged


def test_idempotency(temp_project, monkeypatch):
    project = temp_project
    mod = import_ctr(
        Path(__file__).resolve().parents[1] / "scripts" / "convert_to_relative.py"
    )

    chapter = project / "manuscript" / "chapters" / "p.md"
    pic = project / "assets" / "img" / "p.png"
    write(pic, "png")
    rel = Path(os.path.relpath(pic, start=chapter.parent)).as_posix()
    write(chapter, f"![x]({rel})")

    monkeypatch.setattr(mod, "PROJECT_ROOT", project.resolve(), raising=False)
    monkeypatch.setattr(mod, "ASSETS_DIR", project / "assets", raising=False)

    once = mod.convert_paths_in_text(chapter.read_text(), chapter)
    twice = mod.convert_paths_in_text(once, chapter)
    assert once == twice
