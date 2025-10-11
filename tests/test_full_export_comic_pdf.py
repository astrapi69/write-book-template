# tests/test_full_export_comic_pdf.py
from pathlib import Path
from unittest.mock import patch
import scripts.full_export_comic as fec
import subprocess


def test_export_pdf_success_invokes_pandoc(tmp_path: Path):
    html = tmp_path / "book.html"
    pdf = tmp_path / "book.pdf"
    html.write_text("<html><body>ok</body></html>", encoding="utf-8")

    with patch("scripts.full_export_comic.subprocess.run") as run:
        run.return_value = None  # no exception -> success
        ok = fec.export_pdf_from_html(str(html), str(pdf), pdf_engine="lualatex")
        assert ok is True

        # Verify expected args subset (don’t over-specify order beyond what the function guarantees)
        expected = [
            "pandoc",
            str(html),
            "-o",
            str(pdf),
            "--pdf-engine",
            "lualatex",
        ]
        # Ensure the beginning of the command matches (rest are -V mainfont/monofont)
        actual = run.call_args.args[0]
        assert actual[: len(expected)] == expected


def test_export_pdf_failure_returns_false(tmp_path: Path):
    html = tmp_path / "book.html"
    pdf = tmp_path / "book.pdf"
    html.write_text("<html><body>ok</body></html>", encoding="utf-8")

    with patch("scripts.full_export_comic.subprocess.run") as run:
        run.side_effect = subprocess.CalledProcessError(1, "pandoc")
        ok = fec.export_pdf_from_html(str(html), str(pdf))
        assert ok is False
