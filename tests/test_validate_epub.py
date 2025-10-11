# tests/test_validate_epub.py
import scripts.validate_format as vf


class Dummy:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


def test_epub_success(monkeypatch, tmp_path):
    p = tmp_path / "b.epub"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: True)
    monkeypatch.setattr(vf, "run_cmd", lambda cmd, timeout=None: (0, "OK", ""))

    rc = vf.validate_epub_with_epubcheck(str(p))
    assert rc == 0


def test_epub_issues(monkeypatch, tmp_path, capsys):
    p = tmp_path / "b.epub"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: True)
    monkeypatch.setattr(vf, "run_cmd", lambda cmd, timeout=None: (1, "problems", ""))
    rc = vf.validate_epub_with_epubcheck(str(p))
    assert rc == 1
    out = capsys.readouterr().out
    assert "found issues" in out and "problems" in out


def test_epub_missing_binary(monkeypatch, tmp_path):
    p = tmp_path / "b.epub"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: False)
    rc = vf.validate_epub_with_epubcheck(str(p))
    assert rc == 127


def test_epub_timeout(monkeypatch, tmp_path):
    p = tmp_path / "b.epub"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: True)
    monkeypatch.setattr(vf, "run_cmd", lambda cmd, timeout=None: (124, "", "timeout"))
    rc = vf.validate_epub_with_epubcheck(str(p))
    assert rc == 124


def test_epub_missing_input(tmp_path):
    rc = vf.validate_epub_with_epubcheck(str(tmp_path / "no.epub"))
    assert rc == 2
