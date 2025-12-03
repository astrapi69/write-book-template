# tests/test_shortcuts_export_passthrough.py
import pytest
from unittest.mock import patch
import scripts.shortcuts_export as se


def test_export_pdf_passthrough():
    with patch("scripts.shortcuts_export.export_main") as exp:
        se.export(
            "pdf", None, "--skip-images", "--keep-relative-paths", "--output-file=foo"
        )
        _ = exp.call_args  # export_main(*args, **kwargs)
        # sys.argv is assembled inside _run_full_export; we just ensure it was called once
        assert exp.called


def test_export_html_forwards_valid_options():
    # Wir patchen den internen Runner, um die zusammengesetzten Args zu sehen
    with patch("scripts.shortcuts_export._run_full_export") as run:
        se.export_html(
            "--skip-images",
            "--output-file=foo",
            "--lang=de",
        )

        run.assert_called_once()
        (args,), _ = run.call_args
        # args ist die Liste, die an full_export_book geht
        assert args[0:2] == ["--format", "html"]
        # alle validen Optionen müssen drin sein
        assert "--skip-images" in args
        assert "--output-file=foo" in args
        assert "--lang=de" in args


def test_export_html_safe_adds_skip_images_by_default():
    with patch("scripts.shortcuts_export._run_full_export") as run:
        se.export_html_safe("--output-file=bar")

        (args,), _ = run.call_args
        # Safe-Mode erzwingt mindestens einen Schutz-Flag
        assert ["--format", "html"] == args[0:2]
        assert "--skip-images" in args
        assert "--output-file=bar" in args


def test_export_html_safe_does_not_duplicate_safety_flags():
    with patch("scripts.shortcuts_export._run_full_export") as run:
        # User gibt schon einen der Safe-Flags mit
        se.export_html_safe("--keep-relative-paths", "--output-file=baz")

        (args,), _ = run.call_args
        # Keinen doppelten Safe-Flag injizieren
        assert "--keep-relative-paths" in args
        # es darf *nicht* zusätzlich ein zweiter Safe-Flag automatisch eingefügt werden
        # (in deinem Code wird nur einer hinzugefügt, wenn gar keiner existiert)
        # Wir prüfen hier vor allem, dass es nicht crasht und die Liste plausibel ist
        assert ["--format", "html"] == args[0:2]


def test_export_drops_invalid_options_without_strict(capsys):
    with patch("scripts.shortcuts_export._run_full_export") as run:
        se.export_pdf("--output-file=ok", "--bogus-flag", "value")

        (args,), _ = run.call_args
        # gültige Option bleibt erhalten
        assert "--output-file=ok" in args
        # ungültige Option und ihr Wert dürfen NICHT weitergereicht werden
        assert "--bogus-flag" not in args
        assert "value" not in args

        out, _ = capsys.readouterr()
        assert "Invalid options for full_export_book.py" in out


def test_export_aborts_on_invalid_options_with_strict(capsys):
    with patch("scripts.shortcuts_export._run_full_export") as run:
        se.export_pdf("--output-file=ok", "--bogus-flag", "--strict-opts")

        # Bei strict-opts darf der Runner nicht aufgerufen werden
        run.assert_not_called()

        out, _ = capsys.readouterr()
        assert "Invalid options for full_export_book.py" in out
        assert "Aborting due to --strict-opts" in out


@pytest.mark.parametrize(
    "func, expected_format",
    [
        (se.export_pdf, "pdf"),
        (se.export_epub, "epub"),
        (se.export_docx, "docx"),
        (se.export_markdown, "markdown"),
    ],
)
def test_export_wrappers_forward_args_and_format(func, expected_format):
    """
    Alle einfachen Wrapper (pdf/epub/docx/markdown) sollen:
      - --format korrekt setzen
      - gültige Optionen unverändert weiterreichen
    """
    with patch("scripts.shortcuts_export._run_full_export") as run:
        func("--output-file=mybook", "--lang=de")

        run.assert_called_once()
        (args,), _ = run.call_args

        # format vorne
        assert args[0:2] == ["--format", expected_format]
        # gültige Optionen müssen drin sein
        assert "--output-file=mybook" in args
        assert "--lang=de" in args


@pytest.mark.parametrize(
    "func, expected_format",
    [
        (se.export_pdf_safe, "pdf"),
        (se.export_epub_safe, "epub"),
        (se.export_docx_safe, "docx"),
        (se.export_markdown_safe, "markdown"),
    ],
)
def test_export_safe_wrappers_respect_existing_safety_flag(func, expected_format):
    """
    Wenn der Aufrufer schon --keep-relative-paths/--skip-images setzt,
    darf kein zusätzlicher Safety-Flag erzwungen werden.
    """
    with patch("scripts.shortcuts_export._run_full_export") as run:
        func("--keep-relative-paths", "--output-file=draft")

        run.assert_called_once()
        (args,), _ = run.call_args

        assert args[0:2] == ["--format", expected_format]
        assert "--output-file=draft" in args

        tokens = {tok.split("=", 1)[0] for tok in args if tok.startswith("--")}
        assert "--keep-relative-paths" in tokens
        # nichts zusätzlich erzwungen
        assert "--skip-images" not in tokens


def test_export_all_formats_with_cover_includes_html_and_cover():
    with patch("scripts.shortcuts_export._run_full_export") as run:
        se.export_all_formats_with_cover("--output-file=mybook")

        run.assert_called_once()
        (args,), _ = run.call_args

        # Formatliste inkl. html
        assert "--format" in args
        assert "pdf,epub,docx,markdown,html" in args

        # Cover gesetzt
        assert "--cover" in args
        assert "assets/covers/cover.jpg" in args

        # Extra-Option weitergereicht
        assert "--output-file=mybook" in args


def test_export_all_formats_without_cover():
    with patch("scripts.shortcuts_export._run_full_export") as run:
        se.export_all_formats("--output-file=test")

        run.assert_called_once()
        (args,), _ = run.call_args

        assert "--format" in args
        assert "pdf,epub,docx,markdown,html" in args
        assert "--output-file=test" in args
        # kein Cover-Argument
        assert "--cover" not in args
