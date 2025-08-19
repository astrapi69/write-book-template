from pathlib import Path
import pytest
import scripts.print_version_build as bp

class DummyProc:
    def __init__(self, rc=0): self.returncode = rc

def make_dummy_scripts(dirpath: Path):
    (dirpath / "strip_links.py").write_text("print('strip')", encoding="utf-8")
    (dirpath / "convert_links_to_plain_text.py").write_text("print('plain')", encoding="utf-8")
    (dirpath / "full_export_book.py").write_text("print('export')", encoding="utf-8")

def test_pipeline_order_and_success(monkeypatch, tmp_path, capsys):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    make_dummy_scripts(scripts_dir)

    calls = []
    def fake_run(cmd, check=True):
        calls.append(cmd)
        return DummyProc(0)
    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    # Expect git restore to run at end
    argv = ["--scripts-dir", str(scripts_dir)]
    with pytest.raises(SystemExit) as ex:
        bp.main(argv)
    assert ex.value.code == 0

    # Verify order: three python invocations, then git restore
    py = [c for c in calls if c and c[0].endswith("python") or c[0].endswith("python3") or c[0].endswith("python.exe") or "python" in c[0]]
    assert len(py) == 3
    # last call is 'git restore .'
    assert calls[-1][:2] == ["git", "restore"]

def test_pipeline_aborts_on_failure(monkeypatch, tmp_path, capsys):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    make_dummy_scripts(scripts_dir)

    def fake_run(cmd, check=True):
        # Fail on second script
        if "convert_links_to_plain_text.py" in cmd[1]:
            raise bp.subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return DummyProc(0)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    argv = ["--scripts-dir", str(scripts_dir), "--no-restore"]
    with pytest.raises(SystemExit) as ex:
        bp.main(argv)
    assert ex.value.code == 1

    out, _ = capsys.readouterr()
    assert "Build process aborted." in out
    # Ensure we did NOT try to export or restore
    assert "full_export_book.py" not in out
    assert "Reverting modified files" not in out

def test_pipeline_dry_run_skips_execution_and_restores(monkeypatch, tmp_path, capsys):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    make_dummy_scripts(scripts_dir)

    called = {"run": 0}
    def fake_run(cmd, check=True):
        called["run"] += 1
        return DummyProc(0)
    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as ex:
        bp.main(["--scripts-dir", str(scripts_dir), "--dry-run"])
    assert ex.value.code == 0

    # No subprocess.run should be invoked for python scripts or git in dry-run
    assert called["run"] == 0
    out, _ = capsys.readouterr()
    assert "[dry-run] Would run:" in out
