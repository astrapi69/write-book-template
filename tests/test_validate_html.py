# tests/test_validate_html.py
import pytest
import scripts.validate_format as vf


def test_html_valid(tmp_path, capsys):
    p = tmp_path / "ok.html"
    p.write_text(
        "<!doctype html><html><head><title>x</title></head><body>hi</body></html>",
        encoding="utf-8",
    )
    rc = vf.validate_html(str(p))
    assert rc == 0
    out = capsys.readouterr().out
    assert "HTML exported" in out


def test_html_empty(tmp_path, capsys):
    p = tmp_path / "empty.html"
    p.write_text("", encoding="utf-8")
    rc = vf.validate_html(str(p))
    assert rc == 1
    out = capsys.readouterr().out
    assert "HTML file is empty" in out


def test_html_missing(tmp_path, capsys):
    rc = vf.validate_html(str(tmp_path / "nope.html"))
    assert rc == 2


def test_html_malformed_no_root_tag(tmp_path, capsys):
    p = tmp_path / "bad.html"
    p.write_text(
        "<head><title>no root</title></head><body>content</body>", encoding="utf-8"
    )
    rc = vf.validate_html(str(p))
    assert rc == 1
    out = capsys.readouterr().out
    assert "may be malformed" in out or "malformed" in out


# --- CLI behaviour for HTML ---------------------------------------------------


def test_cli_autodetect_html(tmp_path, capsys):
    p = tmp_path / "auto.html"
    p.write_text("<html>y</html>", encoding="utf-8")
    with pytest.raises(SystemExit) as ex:
        vf.main([str(p)])
    assert ex.value.code == 0
    assert "HTML exported" in capsys.readouterr().out


def test_cli_force_type_html_overrides_extension(tmp_path):
    p = tmp_path / "weird.ext"
    p.write_text("<html>z</html>", encoding="utf-8")
    with pytest.raises(SystemExit) as ex:
        vf.main([str(p), "--type", "html"])
    assert ex.value.code == 0
