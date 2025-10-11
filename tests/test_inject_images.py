# tests/test_inject_images.py
from __future__ import annotations

import json

import pytest

import scripts.inject_images as mod


# ---------- Prompt loading ----------


def test_load_prompts_flat_ok(tmp_path):
    pf = tmp_path / "prompts.json"
    pf.write_text(
        json.dumps({"prompts": [{"filename": "01-intro.png"}]}), encoding="utf-8"
    )
    items = mod.load_prompts(pf)
    assert items == [{"filename": "01-intro.png"}]


def test_load_prompts_nested_ok(tmp_path):
    pf = tmp_path / "prompts.json"
    pf.write_text(
        json.dumps({"chapters": [{"prompts": [{"filename": "chapter_02-hero.png"}]}]}),
        encoding="utf-8",
    )
    items = mod.load_prompts(pf)
    assert items == [{"filename": "chapter_02-hero.png"}]


def test_load_prompts_invalid_json(tmp_path):
    pf = tmp_path / "prompts.json"
    pf.write_text("{ invalid", encoding="utf-8")
    with pytest.raises(ValueError):
        mod.load_prompts(pf)


def test_load_prompts_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        mod.load_prompts(tmp_path / "nope.json")


# ---------- Key extraction & mapping ----------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("01-intro.png", "01"),
        ("chapter_2-cover.png", "02"),
        ("03.png", "03"),
        ("ch-9-foo.png", "09"),
        ("no-number.png", ""),
    ],
)
def test_chapter_key_from_filename(name, expected):
    assert mod.chapter_key_from_filename(name) == expected


def test_build_filename_map_collects_two_digit_keys():
    prompts = [{"filename": "01-intro.png"}, {"filename": "chapter_2-cover.png"}]
    mapping = mod.build_filename_map(prompts)
    assert mapping == {"01": "01-intro.png", "02": "chapter_2-cover.png"}


# ---------- Injection detection & placement ----------


def test_link_already_present_detects_by_basename():
    content = "Intro\n\n![alt](../../assets/illustrations/01-intro.png)\n"
    assert mod.link_already_present(content, "01-intro.png") is True


def test_inject_image_after_h1_and_not_duplicate(tmp_path):
    md = "# Title\n\nSome text.\n"
    rel = "assets/illustrations/01-intro.png"
    new, injected = mod.inject_image(md, rel)
    assert injected is True
    # now re-run should not inject again
    newer, injected2 = mod.inject_image(new, rel)
    assert injected2 is False
    assert new.count("![") == 1


def test_inject_image_at_top_when_no_h1():
    md = "First line\nSecond line\n"
    rel = "assets/illustrations/x.png"
    new, injected = mod.inject_image(md, rel, alt_text="An image")
    assert injected is True
    assert new.splitlines()[0].startswith("![")


def test_compute_relative_path(tmp_path):
    ch = tmp_path / "manuscript" / "chapters"
    img = tmp_path / "assets" / "illustrations"
    ch.mkdir(parents=True)
    img.mkdir(parents=True)
    chapter = ch / "01-intro.md"
    chapter.write_text("# T\n", encoding="utf-8")
    image = img / "01-intro.png"
    image.write_bytes(b"x")
    rel = mod.compute_relative_image_path(chapter, image)
    # from manuscript/chapters to assets/illustrations
    assert rel.replace("\\", "/").endswith("assets/illustrations/01-intro.png")


# ---------- End-to-end process ----------


def _mk_tree(tmp_path):
    ch_dir = tmp_path / "manuscript" / "chapters"
    img_dir = tmp_path / "assets" / "illustrations"
    ch_dir.mkdir(parents=True)
    img_dir.mkdir(parents=True)
    return ch_dir, img_dir


def test_process_injects_when_available(tmp_path):
    ch_dir, img_dir = _mk_tree(tmp_path)
    # chapters
    (ch_dir / "01-intro.md").write_text("# Intro\n\nText\n", encoding="utf-8")
    (ch_dir / "02-next.md").write_text("# Next\n\nText\n", encoding="utf-8")
    # images
    (img_dir / "01-intro.png").write_bytes(b"a")
    (img_dir / "chapter_02-hero.png").write_bytes(b"b")
    # prompts (nested)
    pf = tmp_path / "prompts.json"
    pf.write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "prompts": [
                            {"filename": "01-intro.png"},
                            {"filename": "chapter_02-hero.png"},
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    stats = mod.process(ch_dir, img_dir, pf, dry_run=False)
    assert stats.total == 2
    assert stats.injected == 2
    assert stats.skipped_existing == 0
    assert stats.missing_prompt == 0
    assert stats.missing_image == 0

    c1 = (ch_dir / "01-intro.md").read_text(encoding="utf-8")
    c2 = (ch_dir / "02-next.md").read_text(encoding="utf-8")
    assert "![01-intro]" in c1 or "![01-intro.png]" in c1 or "!(" in c1
    assert "assets/illustrations/01-intro.png" in c1
    assert "assets/illustrations/chapter_02-hero.png" in c2


def test_process_skips_if_already_present(tmp_path, capsys):
    ch_dir, img_dir = _mk_tree(tmp_path)
    md = "# Intro\n\n![x](../../assets/illustrations/01-intro.png)\n"
    (ch_dir / "01-intro.md").write_text(md, encoding="utf-8")
    (img_dir / "01-intro.png").write_bytes(b"a")
    pf = tmp_path / "prompts.json"
    pf.write_text(
        json.dumps({"prompts": [{"filename": "01-intro.png"}]}), encoding="utf-8"
    )

    stats = mod.process(ch_dir, img_dir, pf, dry_run=False)
    assert stats.injected == 0
    assert stats.skipped_existing == 1
    out = capsys.readouterr().out
    assert "Already contains image" in out


def test_process_counts_missing_prompt_and_image(tmp_path, capsys):
    ch_dir, img_dir = _mk_tree(tmp_path)
    (ch_dir / "01-intro.md").write_text("# Intro\n", encoding="utf-8")
    (ch_dir / "03-other.md").write_text("# Other\n", encoding="utf-8")
    # only one prompt for chapter 01 but file missing
    pf = tmp_path / "prompts.json"
    pf.write_text(
        json.dumps({"prompts": [{"filename": "01-intro.png"}]}), encoding="utf-8"
    )

    stats = mod.process(ch_dir, img_dir, pf, dry_run=False)
    assert stats.missing_prompt == 1  # for chapter 03
    assert stats.missing_image == 1  # 01 image not present
    out = capsys.readouterr().out
    assert "No image defined" in out
    assert "Image not found" in out


def test_dry_run_does_not_write(tmp_path, capsys):
    ch_dir, img_dir = _mk_tree(tmp_path)
    md_path = ch_dir / "01-intro.md"
    md_path.write_text("# Intro\n\nPara\n", encoding="utf-8")
    (img_dir / "01-intro.png").write_bytes(b"a")
    pf = tmp_path / "prompts.json"
    pf.write_text(
        json.dumps({"prompts": [{"filename": "01-intro.png"}]}), encoding="utf-8"
    )

    _ = mod.process(ch_dir, img_dir, pf, dry_run=True)
    out = capsys.readouterr().out
    assert "Dry-run: would inject" in out
    # content unchanged
    assert md_path.read_text(encoding="utf-8") == "# Intro\n\nPara\n"
