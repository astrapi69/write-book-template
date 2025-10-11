# tests/test_strip_links_cli.py
import scripts.strip_links as sl


def test_cli_missing_file_returns_1(tmp_path, capsys):
    code = sl.main(["--file", str(tmp_path / "missing.md")])
    assert code == 1
    _, err = capsys.readouterr()


def test_cli_dry_run_reports_and_writes_nothing(tmp_path, capsys):
    f = tmp_path / "toc.md"
    f.write_text("See [X](Y)", encoding="utf-8")
    code = sl.main(["--file", str(f), "--dry-run", "--report"])
    assert code == 0
    out, _ = capsys.readouterr()
    assert "links_stripped=1" in out
    assert "dry-run" in out
    # no new file
    assert not (tmp_path / "toc-nolinks.md").exists()


def test_cli_copy_mode_writes_suffix(tmp_path, capsys):
    f = tmp_path / "toc.md"
    f.write_text("Link [A](B)", encoding="utf-8")
    code = sl.main(["--file", str(f), "--report"])
    assert code == 0
    out, _ = capsys.readouterr()
    assert "→ toc-nolinks.md" in out
    assert (tmp_path / "toc-nolinks.md").read_text(encoding="utf-8") == "Link A"


def test_cli_overwrite(tmp_path, capsys):
    f = tmp_path / "toc.md"
    f.write_text("Link [A](B)", encoding="utf-8")
    code = sl.main(["--file", str(f), "--overwrite", "--report"])
    assert code == 0
    out, _ = capsys.readouterr()
    assert "in place" in out
    assert f.read_text(encoding="utf-8") == "Link A"
