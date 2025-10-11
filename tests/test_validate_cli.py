# tests/test_validate_cli.py
import pytest
import scripts.validate_format as vf


def test_cli_autodetect_md(tmp_path, capsys):
    p = tmp_path / "a.md"
    p.write_text("x")
    with pytest.raises(SystemExit) as ex:
        vf.main([str(p)])
    assert ex.value.code == 0
    assert "Markdown exported" in capsys.readouterr().out


def test_cli_forced_type_overrides_extension(tmp_path, monkeypatch):
    p = tmp_path / "a.weird"
    p.write_text("x")
    # force md; should work
    with pytest.raises(SystemExit) as ex:
        vf.main([str(p), "--type", "md"])
    assert ex.value.code == 0


def test_cli_unknown_type(tmp_path, capsys):
    p = tmp_path / "a.weird"
    p.write_text("x")
    with pytest.raises(SystemExit):
        vf.main([str(p), "--type", "xyz"])  # argparse will reject before main
    # If we ever reach here, argparse would have exited with code 2
