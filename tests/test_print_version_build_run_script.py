# tests/test_print_version_build_run_script.py
import scripts.print_version_build as bp


class DummyProc:
    def __init__(self, rc=0):
        self.returncode = rc


def test_run_script_success(monkeypatch, tmp_path):
    s = tmp_path / "ok.py"
    s.write_text("print('hi')", encoding="utf-8")

    def fake_run(cmd, check=True):
        assert str(s) in cmd
        return DummyProc(0)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    assert bp.run_script(s) is True


def test_run_script_failure(monkeypatch, tmp_path, capsys):
    s = tmp_path / "boom.py"
    s.write_text("raise SystemExit(1)", encoding="utf-8")

    class Boom(Exception):
        pass

    def fake_run(cmd, check=True):
        raise bp.subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    assert bp.run_script(s) is False
    out, _ = capsys.readouterr()
    assert "Command failed with exit code" in out


def test_run_script_missing(tmp_path, capsys):
    missing = tmp_path / "nope.py"
    assert bp.run_script(missing) is False
    out, _ = capsys.readouterr()
    assert "Script not found" in out


def test_run_script_dry_run(monkeypatch, tmp_path, capsys):
    s = tmp_path / "ok.py"
    s.write_text("print('x')", encoding="utf-8")
    called = {"run": False}

    def fake_run(*a, **k):
        called["run"] = True
        return DummyProc(0)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)
    assert bp.run_script(s, "--foo=1", dry_run=True) is True
    assert called["run"] is False
    out, _ = capsys.readouterr()
    assert "[dry-run] Would run:" in out
