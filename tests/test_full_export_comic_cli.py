# tests/test_full_export_comic_cli.py
from pathlib import Path
import scripts.full_export_comic as fec


def test_cli_main_success_html_only(tmp_path: Path):
    chapters = tmp_path / "chapters"
    outdir = tmp_path / "out"
    chapters.mkdir()
    (chapters / "01.html").write_text("<body>A</body>", encoding="utf-8")

    code = fec.main(
        [
            "--chapter-dir",
            str(chapters),
            "--output-html",
            str(outdir / "book.html"),
            "--title",
            "TestBook",
            "--lang",
            "de",
        ]
    )
    assert code == 0
    assert (outdir / "book.html").exists()
