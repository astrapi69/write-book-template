# tests/test_images_integration.py
from __future__ import annotations

import json
from pathlib import Path
from typing import FrozenSet


import scripts.generate_images_deepai as gen
import scripts.inject_images as inj


# --- helpers -----------------------------------------------------------------


def mk_project_tree(tmp_path: Path):
    chapters = tmp_path / "manuscript" / "chapters"
    images = tmp_path / "assets" / "illustrations"
    scripts_data = tmp_path / "scripts" / "data"
    prompt_file = scripts_data / "image_prompts.json"
    chars_file = scripts_data / "character_profiles.json"

    chapters.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    scripts_data.mkdir(parents=True, exist_ok=True)

    return chapters, images, prompt_file, chars_file


def fake_generate_image_factory(fail_on: FrozenSet[str] = frozenset()):
    """
    Returns a fake generate_image(**kwargs) that writes a file (simulating success),
    unless filename is in fail_on (then return False without writing).
    Also respects overwrite flag.
    """
    calls = []

    def fake_generate_image(
        *,
        session,
        prompt,
        filename,
        output_dir,
        api_key,
        endpoint=gen.DEEPAI_ENDPOINT,
        timeout=30,
        overwrite=False,
    ):
        calls.append(
            {
                "filename": filename,
                "output_dir": output_dir,
                "overwrite": overwrite,
                "prompt": prompt,
            }
        )
        output_path = Path(output_dir) / filename
        if filename in fail_on:
            return False
        if output_path.exists() and not overwrite:
            return True
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"FAKEPNG")
        return True

    return fake_generate_image, calls


# --- tests -------------------------------------------------------------------


def test_integration_generate_then_inject_happy_path(tmp_path, monkeypatch):
    # Arrange project tree
    chapters_dir, images_dir, prompt_file, chars_file = mk_project_tree(tmp_path)

    # Chapters
    (chapters_dir / "01-intro.md").write_text("# Intro\n\nText\n", encoding="utf-8")
    (chapters_dir / "02-next.md").write_text("# Next\n\nText\n", encoding="utf-8")

    # Prompts (nested structure used by generator)
    prompt_file.write_text(
        json.dumps(
            {
                "style": "cinematic",
                "chapters": [
                    {
                        "prompts": [
                            {
                                "filename": "01-intro.png",
                                "character": "Timmy",
                                "prompt": "village gate",
                            },
                            {
                                "filename": "chapter_02-hero.png",
                                "character": ["Timmy", "Boronius"],
                                "prompt": "old tree",
                            },
                        ]
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    # Character profiles (used by generator; not needed by injector)
    chars_file.write_text(
        json.dumps({"Timmy": "Timmy brave", "Boronius": "Boronius wise"}),
        encoding="utf-8",
    )

    # Stub DeepAI call
    fake_gen, calls = fake_generate_image_factory()
    monkeypatch.setattr(gen, "generate_image", fake_gen)
    monkeypatch.setenv("DEEPAI_API_KEY", "XYZ")

    # Act 1: run generator (writes images)
    rc = gen.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--character-profile",
            str(chars_file),
            "--output-dir",
            str(images_dir),
        ]
    )
    assert rc == 0
    assert (images_dir / "01-intro.png").exists()
    assert (images_dir / "chapter_02-hero.png").exists()

    # Act 2: run injector (inserts into chapters)
    stats = inj.process(chapters_dir, images_dir, prompt_file, dry_run=False)
    assert stats.total == 2
    assert stats.injected == 2
    assert stats.missing_prompt == 0
    assert stats.missing_image == 0

    # Assert links are correct relative paths
    c1 = (chapters_dir / "01-intro.md").read_text(encoding="utf-8")
    c2 = (chapters_dir / "02-next.md").read_text(encoding="utf-8")
    assert "assets/illustrations/01-intro.png" in c1
    assert "assets/illustrations/chapter_02-hero.png" in c2

    # Also verify the composed prompts reached the generator (integration aspect)
    prompts_sent = [c["prompt"] for c in calls]
    assert any(
        "Timmy brave" in p and "village gate" in p and "cinematic" in p
        for p in prompts_sent
    )
    assert any(
        "Timmy brave" in p
        and "Boronius wise" in p
        and "old tree" in p
        and "cinematic" in p
        for p in prompts_sent
    )


def test_integration_skip_existing_and_skip_injection_if_present(
    tmp_path, monkeypatch, capsys
):
    chapters_dir, images_dir, prompt_file, chars_file = mk_project_tree(tmp_path)

    # Chapter already contains link → injector should skip
    (chapters_dir / "01-intro.md").write_text(
        "# Intro\n\n![x](../../assets/illustrations/01-intro.png)\n", encoding="utf-8"
    )

    # Prompts
    prompt_file.write_text(
        json.dumps(
            {"chapters": [{"prompts": [{"filename": "01-intro.png", "prompt": "p"}]}]}
        ),
        encoding="utf-8",
    )

    # Profiles (not used by injector; required by generator)
    chars_file.write_text("{}", encoding="utf-8")

    # First generation: creates file
    fake_gen, calls = fake_generate_image_factory()
    monkeypatch.setattr(gen, "generate_image", fake_gen)
    monkeypatch.setenv("DEEPAI_API_KEY", "XYZ")

    rc1 = gen.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--character-profile",
            str(chars_file),
            "--output-dir",
            str(images_dir),
        ]
    )
    assert rc1 == 0
    assert (images_dir / "01-intro.png").exists()

    # Second generation without --overwrite should "skip" (fake honors existence)
    rc2 = gen.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--character-profile",
            str(chars_file),
            "--output-dir",
            str(images_dir),
        ]
    )
    assert rc2 == 0

    # Now injector should detect already-present link
    stats = inj.process(chapters_dir, images_dir, prompt_file, dry_run=False)
    assert stats.injected == 0
    assert stats.skipped_existing == 1
    out = capsys.readouterr().out
    assert "Already contains image" in out


def test_integration_partial_failure_in_generation_reflected_in_inject(
    tmp_path, monkeypatch, capsys
):
    chapters_dir, images_dir, prompt_file, chars_file = mk_project_tree(tmp_path)

    # Chapters
    (chapters_dir / "01-intro.md").write_text("# Intro\n", encoding="utf-8")
    (chapters_dir / "02-next.md").write_text("# Next\n", encoding="utf-8")

    # Prompts (two images)
    prompt_file.write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "prompts": [
                            {"filename": "01-intro.png", "prompt": "ok"},
                            {"filename": "02-next.png", "prompt": "will-fail"},
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    # Profiles
    chars_file.write_text("{}", encoding="utf-8")

    # Fake generate: fail on "02-next.png"
    fake_gen, _ = fake_generate_image_factory(fail_on={"02-next.png"})
    monkeypatch.setattr(gen, "generate_image", fake_gen)
    monkeypatch.setenv("DEEPAI_API_KEY", "XYZ")

    # Run generator (only first image gets written)
    rc = gen.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--character-profile",
            str(chars_file),
            "--output-dir",
            str(images_dir),
        ]
    )
    assert rc == 1  # generation reported a failure
    assert (images_dir / "01-intro.png").exists()
    assert not (images_dir / "02-next.png").exists()

    # Inject: first will be injected, second counted as missing image
    stats = inj.process(chapters_dir, images_dir, prompt_file, dry_run=False)
    assert stats.injected == 1
    assert stats.missing_image == 1
    assert stats.missing_prompt == 0
    out = capsys.readouterr().out
    assert "Image not found" in out


def test_integration_overwrite_true_regenerates_file_but_injection_stable(
    tmp_path, monkeypatch
):
    chapters_dir, images_dir, prompt_file, chars_file = mk_project_tree(tmp_path)

    # Chapter with no image yet
    md_path = chapters_dir / "01-intro.md"
    md_path.write_text("# Intro\n\nPara\n", encoding="utf-8")

    prompt_file.write_text(
        json.dumps(
            {"chapters": [{"prompts": [{"filename": "01-intro.png", "prompt": "p"}]}]}
        ),
        encoding="utf-8",
    )
    chars_file.write_text("{}", encoding="utf-8")

    # Fake generate
    fake_gen, _ = fake_generate_image_factory()
    monkeypatch.setattr(gen, "generate_image", fake_gen)
    monkeypatch.setenv("DEEPAI_API_KEY", "XYZ")

    # Initial generate + inject
    assert (
        gen.main(
            [
                "--prompt-file",
                str(prompt_file),
                "--character-profile",
                str(chars_file),
                "--output-dir",
                str(images_dir),
            ]
        )
        == 0
    )
    inj.process(chapters_dir, images_dir, prompt_file, dry_run=False)
    content1 = md_path.read_text(encoding="utf-8")

    # Regenerate with --overwrite (should rewrite image file but not duplicate link)
    assert (
        gen.main(
            [
                "--prompt-file",
                str(prompt_file),
                "--character-profile",
                str(chars_file),
                "--output-dir",
                str(images_dir),
                "--overwrite",
            ]
        )
        == 0
    )
    # Running injection again should detect duplicate and not add another line
    stats = inj.process(chapters_dir, images_dir, prompt_file, dry_run=False)
    assert stats.skipped_existing == 1
    content2 = md_path.read_text(encoding="utf-8")
    assert content2 == content1  # injection stable
