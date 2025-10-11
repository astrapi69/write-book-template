# tests/test_bulk_change_extension.py
from pathlib import Path
import subprocess
import sys

from scripts.bulk_change_extension import change_extension  # <- fixed import


def make_files(base: Path, names):
    base.mkdir(parents=True, exist_ok=True)
    for n in names:
        p = base / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"data")


def test_happy_path_png_to_jpg(tmp_path: Path):
    make_files(tmp_path, ["a.png", "b.PNG", "c.jpg", "note.txt"])
    res = change_extension(tmp_path, ".png", ".jpg", recursive=False)
    assert res.renamed == 2
    assert (tmp_path / "a.jpg").exists()
    assert (tmp_path / "b.jpg").exists()
    assert (tmp_path / "c.jpg").exists()
    assert res.errors == 0


def test_case_sensitive_only_exact_match(tmp_path: Path):
    make_files(tmp_path, ["A.png", "B.PNG", "C.PnG"])
    res = change_extension(
        tmp_path, ".png", ".jpg", recursive=False, case_insensitive=False
    )
    assert res.renamed == 1
    assert (tmp_path / "A.jpg").exists()
    assert (tmp_path / "B.PNG").exists()
    assert (tmp_path / "C.PnG").exists()


def test_recursive_subdirs(tmp_path: Path):
    make_files(tmp_path, ["a.png", "sub/inner.png", "sub/deeper/leaf.PNG"])
    res = change_extension(tmp_path, "png", "jpg", recursive=True)
    assert res.renamed == 3
    assert (tmp_path / "a.jpg").exists()
    assert (tmp_path / "sub/inner.jpg").exists()
    assert (tmp_path / "sub/deeper/leaf.jpg").exists()


def test_conflict_skips_when_overwrite_false(tmp_path: Path):
    make_files(tmp_path, ["x.png", "x.jpg"])
    res = change_extension(tmp_path, "png", "jpg", overwrite=False)
    assert res.renamed == 0
    assert res.skipped_conflict == 1
    assert (tmp_path / "x.png").exists()
    assert (tmp_path / "x.jpg").exists()


def test_conflict_overwrite_true(tmp_path: Path):
    make_files(tmp_path, ["y.png", "y.jpg"])
    (tmp_path / "y.jpg").write_bytes(b"old")
    res = change_extension(tmp_path, "png", "jpg", overwrite=True)
    assert res.renamed == 1
    assert not (tmp_path / "y.png").exists()
    assert (tmp_path / "y.jpg").exists()


def test_dry_run_does_not_change_files(tmp_path: Path):
    make_files(tmp_path, ["d1.png", "d2.PNG"])
    res = change_extension(tmp_path, "png", "jpg", dry_run=True)
    assert res.planned == 2
    assert res.renamed == 0
    assert (tmp_path / "d1.png").exists()
    assert (tmp_path / "d2.PNG").exists()
    assert not (tmp_path / "d1.jpg").exists()


def test_directory_does_not_exist_is_error(tmp_path: Path):
    missing = tmp_path / "nope"
    res = change_extension(missing, "png", "jpg")
    assert res.errors == 1
    assert res.renamed == 0


def test_cli_smoke(tmp_path: Path):
    src = tmp_path / "cli"
    src.mkdir()
    (src / "one.png").write_bytes(b"x")
    cmd = [
        sys.executable,
        "-m",
        "scripts.bulk_change_extension",  # <- run as a module from scripts
        str(src),
        "--from",
        "png",
        "--to",
        "jpg",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True)
    assert out.returncode == 0
    assert (src / "one.jpg").exists()
