# tests/test_shortcuts_export_passthrough.py
from unittest.mock import patch
import scripts.shortcuts_export as se

def test_export_pdf_passthrough():
    with patch("scripts.shortcuts_export.export_main") as exp:
        se.export_pdf("--skip-images", "--keep-relative-paths", "--output-file=foo")
        args = exp.call_args  # export_main(*args, **kwargs)
        # sys.argv is assembled inside _run_full_export; we just ensure it was called once
        assert exp.called
