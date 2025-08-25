# tests/test_pandoc_batch_run_and_main.py
import argparse
from pathlib import Path

import pytest
import scripts.pandoc_batch as mod


class DummyProc:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


@pytest.fixture
def fake_pandoc(monkeypatch):
    # Pretend pandoc exists
    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/pandoc")

    # Intercept subprocess.run to avoid calling real pandoc
    calls = []

    def _run(cmd, capture_output=True, text=True):
        calls.append(cmd)
        # success unless file name contains "fail"
        rc = 1 if any("fail" in str(part) for part in cmd) else 0
        return DummyProc(rc=rc, out="ok", err="")

    monkeypatch.setattr(mod.subprocess, "run", _run)
    return calls


def test_run_one_uses_temp_when_not_inplace(tmp_path, monkeypatch, fake_pandoc):
    f = tmp_path / "in.md"
    f.write_text("---\nNot blank after HR\n", encoding="utf-8")

    # Ensure temp gets created and later removed
    created_paths = []
    real_tmp = mod._create_temp_with

    def spy_create_temp_with(patched: str) -> Path:
        p = real_tmp(patched)
        created_paths.append(p)
        return p

    monkeypatch.setattr(mod, "_create_temp_with", spy_create_temp_with)

    args = argparse.Namespace(
        verbose=False,
        standalone=True,
        from_fmt="markdown",
        to="html",
        metadata_file=None,
        lang=None,
        resource_path=[],
        extra=None,
        patch_md=True,
        fix_inplace=False,
        report_patches=False,
    )
    _, rc, _ = mod.run_one(f, None, args)
    assert rc == 0
    # temp file created and cleaned
    assert created_paths, "expected a temp file"
    for p in created_paths:
        assert not p.exists(), "temp file should be removed"


def test_run_one_inplace_writes_back(tmp_path, fake_pandoc):
    f = tmp_path / "in.md"
    f.write_text("---\nNo blank\nNext\n", encoding="utf-8")

    args = argparse.Namespace(
        verbose=False,
        standalone=True,
        from_fmt="markdown",
        to="html",
        metadata_file=None,
        lang=None,
        resource_path=[],
        extra=None,
        patch_md=True,
        fix_inplace=True,
        report_patches=False,
    )
    before = f.read_text(encoding="utf-8")
    _, rc, _ = mod.run_one(f, None, args)
    after = f.read_text(encoding="utf-8")
    assert rc == 0
    assert after != before
    # Ensure there's a blank line AFTER the HR; since file starts with '---',
    # we should see '---\n\nNo blank'
    assert "---\n\nNo blank" in after


def test_main_end_to_end_test_only(tmp_path, monkeypatch, fake_pandoc, capsys):
    # Create minimal project with pyproject defaults
    root = tmp_path / "manuscript"
    (root / "chap").mkdir(parents=True)
    (root / "chap" / "a.md").write_text("# A", encoding="utf-8")
    (root / "chap" / "b.md").write_text("# B", encoding="utf-8")

    (tmp_path / "pyproject.toml").write_text(
        "[tool.pandoc_batch]\n"
        "root = 'manuscript'\n"
        "outdir = 'output'\n"
        "to = 'html'\n"
        "lang = 'de'\n",
        encoding="utf-8",
    )

    # Run in temp CWD so find_pyproject() sees our file
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(tmp_path)
        argv = ["--test-only", "--jobs", "2"]
        with pytest.raises(SystemExit) as ex:
            mod.main(argv)
        assert ex.value.code == 0

    out, err = capsys.readouterr()
    assert "Starting Pandoc for 2 file(s), format: html, jobs: 2..." in out
    assert "DONE without errors." in out
    assert err == ""


def test_main_reports_failures(tmp_path, monkeypatch, capsys):
    # Make one file whose name triggers rc=1 in fake runner
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "ok.md").write_text("ok", encoding="utf-8")
    (root / "will-fail.md").write_text("x", encoding="utf-8")

    # Avoid pyproject lookup; also make require_cmd a no-op
    monkeypatch.setattr(mod, "require_cmd", lambda _: None)
    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/pandoc")

    def fake_run(cmd, capture_output=True, text=True):
        # Fail only on the real source path; ensure we use --no-patch-md so infile is last arg
        rc = 1 if "will-fail.md" in str(cmd[-1]) else 0
        return DummyProc(rc=rc, out="", err="boom" if rc else "")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    argv = [
        "--root",
        str(root),
        "--outdir",
        str(tmp_path / "out"),
        "--to",
        "html",
        "--test-only",
        "--jobs",
        "1",
        "--no-patch-md",
    ]
    with pytest.raises(SystemExit) as ex:
        mod.main(argv)
    assert ex.value.code == 1

    out, err = capsys.readouterr()
    assert "FAIL" in out
    assert "DONE with 1 failure(s)." in err
