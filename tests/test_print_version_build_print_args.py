# tests/test_print_version_build_print_args.py
import scripts.print_version_build as bp


def test_parse_args_valid_type():
    ns = bp.parse_args(["--book-type", "hardcover"])
    assert ns.book_type == "hardcover"


def test_parse_args_invalid_type_falls_back(capsys):
    ns = bp.parse_args(["--book-type", "stone-tablet"])
    assert ns.book_type == "paperback"
    out, _ = capsys.readouterr()
    assert "Invalid book type" in out


def test_parse_args_defaults_and_flags(tmp_path):
    ns = bp.parse_args(
        [
            "--dry-run",
            "--no-restore",
            "--scripts-dir",
            str(tmp_path),
            "--export-format",
            "epub",
        ]
    )
    assert ns.dry_run is True
    assert ns.no_restore is True
    assert ns.scripts_dir == tmp_path
    assert ns.export_format == "epub"
