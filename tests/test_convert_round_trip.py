# tests/test_convert_round_trip.py
import importlib.util
import os
from pathlib import Path
import textwrap
import pytest


def _import(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None, "ModuleSpec is None"
    assert spec.loader is not None, "ModuleSpec.loader is None"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


@pytest.fixture()
def project(tmp_path: Path):
    root = tmp_path
    (root / "manuscript" / "chapters").mkdir(parents=True)
    (root / "assets" / "img").mkdir(parents=True)
    md = root / "manuscript" / "chapters" / "ch1.md"
    img = root / "assets" / "img" / "p(1) test.png"
    img.write_text("png", encoding="utf-8")
    # from manuscript/chapters to assets/img is two levels up
    md.write_text(
        textwrap.dedent(
            """
            # Ch1
            ![x](../../assets/img/p(1) test.png)
            ![x](<../../assets/img/p(1) test.png> "t")
            """
        ).strip(),
        encoding="utf-8",
    )
    return root, md, img


def test_convert_absolute_then_back_relative_round_trip(project, monkeypatch):
    root, md, img = project

    # Import real modules from repo (not temp copies)
    repo_root = Path(__file__).resolve().parents[1]
    to_abs = _import(
        "convert_to_absolute", repo_root / "scripts" / "convert_to_absolute.py"
    )
    to_rel = _import(
        "convert_to_relative", repo_root / "scripts" / "convert_to_relative.py"
    )

    # Step 1: relative -> absolute
    changed, count = to_abs.convert_file_to_absolute(md)
    assert changed
    assert count >= 2, "Expected both image references to become absolute paths"

    abs_text = md.read_text(encoding="utf-8")
    assert (
        str(img.resolve()) in abs_text
    ), "Absolute path should appear after conversion"

    # Step 2: Patch convert_to_relative to see our temp project as root
    monkeypatch.setattr(to_rel, "PROJECT_ROOT", root.resolve(), raising=False)
    monkeypatch.setattr(to_rel, "ASSETS_DIR", root / "assets", raising=False)

    # Step 3: absolute -> relative
    reverted = to_rel.convert_paths_in_text(abs_text, md)
    expected_rel = Path(os.path.relpath(img, start=md.parent)).as_posix()

    assert f"![x]({expected_rel})" in reverted
    assert f'![x]({expected_rel} "t")' in reverted
