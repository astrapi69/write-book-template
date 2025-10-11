# tests/test_validate_pdf.py
import scripts.validate_format as vf


def test_pdf_success(monkeypatch, tmp_path, capsys):
    p = tmp_path / "a.pdf"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: True)
    monkeypatch.setattr(
        vf, "run_cmd", lambda cmd, timeout=None: (0, "Title: X\nPages: 12\n", "")
    )
    rc = vf.validate_pdf(str(p), timeout=1)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Pages: 12" in out


def test_pdf_failure(monkeypatch, tmp_path, capsys):
    p = tmp_path / "a.pdf"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: True)
    monkeypatch.setattr(vf, "run_cmd", lambda cmd, timeout=None: (1, "", "broken"))
    rc = vf.validate_pdf(str(p))
    assert rc == 1
    assert "broken" in capsys.readouterr().out


def test_pdf_no_pdfinfo(monkeypatch, tmp_path):
    p = tmp_path / "a.pdf"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: False)
    rc = vf.validate_pdf(str(p))
    assert rc == 127


def test_pdf_timeout(monkeypatch, tmp_path):
    p = tmp_path / "a.pdf"
    p.write_text("x")
    monkeypatch.setattr(vf, "require_cmd", lambda _: True)
    monkeypatch.setattr(vf, "run_cmd", lambda cmd, timeout=None: (124, "", "timeout"))
    rc = vf.validate_pdf(str(p))
    assert rc == 124


def test_pdf_missing(tmp_path):
    rc = vf.validate_pdf(str(tmp_path / "no.pdf"))
    assert rc == 2
