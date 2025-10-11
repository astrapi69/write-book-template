# tests/test_validate_docx_and_md.py
import zipfile
import scripts.validate_format as vf


def test_docx_valid(tmp_path):
    p = tmp_path / "x.docx"
    # minimal docx-like zip with [Content_Types].xml
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
    assert vf.validate_docx(str(p)) == 0


def test_docx_invalid_structure(tmp_path):
    p = tmp_path / "x.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("foo.txt", "nope")
    assert vf.validate_docx(str(p)) == 1


def test_docx_corrupted(tmp_path):
    p = tmp_path / "x.docx"
    p.write_text("not a zip")
    rc = vf.validate_docx(str(p))
    assert rc == 1


def test_docx_missing(tmp_path):
    assert vf.validate_docx(str(tmp_path / "no.docx")) == 2


def test_md_nonempty(tmp_path, capsys):
    p = tmp_path / "x.md"
    p.write_text("# ok")
    rc = vf.validate_markdown(str(p))
    assert rc == 0
    assert "exported" in capsys.readouterr().out.lower()


def test_md_empty(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("")
    assert vf.validate_markdown(str(p)) == 1


def test_md_missing(tmp_path):
    assert vf.validate_markdown(str(tmp_path / "no.md")) == 2
