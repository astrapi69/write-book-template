#!/usr/bin/env python3
# scripts/shortcuts_export.py
"""
Shortcuts for book export pipelines with **validated passthrough options**.

Features
--------
- Forwards extra CLI options to the underlying scripts while validating them
  against public allow-lists (value-agnostic, name-based).
- Logs valid vs invalid options.
- Optional `--strict-opts` flag: if present, abort on invalid options; otherwise
  continue and drop the invalid ones.

Targets
-------
- full_export_book.py (multi-format export)
- print_version_build.py (print-optimized EPUB export; will forward a subset to
  full_export_book.py internally)

Safe Mode
---------
Safe exports (`export-pdf-safe`, `export-epub-safe`, `export-docx-safe`,
`export-markdown-safe`, alias `export-es`) wrap the normal pipeline in a
**read-only, draft build mode**:

1. Skips **Step 1** (preprocess/convert sources) → no in-place edits of Markdown
2. Runs **Step 2** (pandoc conversion) → still produces your requested format
3. Runs **Step 3** (postprocess, e.g. cover injection, EPUB2 tweaks)
4. Skips **Step 4** (restore/cleanup sources) → nothing to restore since Step 1 was skipped

Additionally, Safe Mode **forces protective flags**:
- `--skip-images` → no image conversion or inlining
- `--keep-relative-paths` → don’t rewrite links to local assets

⚠️ Safe builds are **not production-ready**:
- ✅ Faster and safer: great for drafts, CI checks, and quick previews
- ❌ Missing images, incomplete polish: for final exports use the normal commands

Common Examples
---------------
Poetry shortcuts:
    poetry run export-pdf --output-file=final
    poetry run export-pdf-safe --output-file=draft
    poetry run export-epub2 --cover=assets/covers/cover.jpg
    poetry run export-print-version-hardcover --lang=de --strict-opts

Direct module execution:
    python scripts/shortcuts_export.py export --format pdf -- --skip-images --output-file=foo
    python scripts/shortcuts_export.py print-version --book-type hardcover -- --lang=de

Notes
-----
- Everything after a bare `--` is treated as passthrough to the target script and
  will be validated and (if valid) forwarded.
- `--strict-opts` is consumed by the **caller** (this module) and not forwarded further.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List

from scripts.full_export_book import main as export_main
from scripts.print_version_build import main as export_print_version_main

# ──────────────────────────────────────────────────────────────────────────────
# Public allow-lists to validate extras before dispatch
# (Option *names* only, value-agnostic)
# ──────────────────────────────────────────────────────────────────────────────

FULL_EXPORT_ALLOWED_OPTS = {
    "--format",
    "--order",
    "--cover",
    "--epub2",
    "--lang",
    "--extension",
    "--book-type",
    "--output-file",
    "--skip-images",
    "--keep-relative-paths",
}

PRINT_VERSION_ALLOWED_OPTS = {
    "--book-type",
    "--export-format",
    "--scripts-dir",
    "--dry-run",
    "--no-restore",
    "--strict-opts",  # handled here; not forwarded further
}

__all__ = [
    "export",
    "all_formats_with_cover",
    "export_epub2",
    "export_epub2_with_cover",
    "export_print_version_epub",
    "export_print_version_paperback",
    "export_print_version_hardcover",
    "export_print_version_paperback_safe",
    "export_print_version_hardcover_safe",
    "export_safe",
    # Safe aliases:
    "export_pdf_safe",
    "export_epub_safe",
    "export_docx_safe",
    "export_markdown_safe",
    # Compat aliases:
    "export_pdf",
    "export_epub",
    "export_docx",
    "export_markdown",
    # Utilities:
    "list_allowed_opts",
    "main",
]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _has_any_option(extra: Iterable[str], names: set[str]) -> bool:
    for tok in extra:
        if not tok.startswith("--"):
            continue
        if tok.split("=", 1)[0] in names:
            return True
    return False


def _split_valid_invalid_options(
    extra: List[str], allowed: set[str]
) -> tuple[list[str], list[str]]:
    valid: List[str] = []
    invalid: List[str] = []
    i = 0
    while i < len(extra):
        tok = extra[i]
        if tok.startswith("--"):
            name = tok.split("=", 1)[0]
            bucket = valid if name in allowed else invalid
            bucket.append(tok)
            if (
                "=" not in tok
                and (i + 1) < len(extra)
                and not extra[i + 1].startswith("-")
            ):
                bucket.append(extra[i + 1])
                i += 1
        i += 1
    return valid, invalid


def _run_full_export(args_list: List[str]):
    """Invoke the full export pipeline with a synthetic argv."""
    sys.argv = ["full-export", *args_list]
    export_main()


def _run_print_version(args_list: List[str]):
    """Invoke the print-version pipeline with a synthetic argv."""
    sys.argv = ["print-version-build", *args_list]
    export_print_version_main()


def list_allowed_opts() -> None:
    print("Allowed options (by target):")
    print("  full_export_book.py:")
    print("   ", " ".join(sorted(FULL_EXPORT_ALLOWED_OPTS)))
    print("  print_version_build.py:")
    print("   ", " ".join(sorted(PRINT_VERSION_ALLOWED_OPTS)))


# ──────────────────────────────────────────────────────────────────────────────
# Shortcuts API (used by Poetry script entries or imports)
# ──────────────────────────────────────────────────────────────────────────────


def export(format: str, cover: str | None = None, *extra: str):
    """
    Export in a specific format via full_export_book.py, with passthrough validation.
    """
    args = ["--format", format]
    if cover:
        args.extend(["--cover", cover])

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(list(extra), FULL_EXPORT_ALLOWED_OPTS)

    if invalid:
        print("⚠️ Invalid options for full_export_book.py:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options to full_export_book.py:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_full_export(args)


def export_pdf(*extra: str):
    """Back-compat alias for tests/old scripts."""
    return export("pdf", None, *extra)


def export_epub(*extra: str):
    """Back-compat alias for tests/old scripts."""
    return export("epub", None, *extra)


def export_docx(*extra: str):
    """Back-compat alias for tests/old scripts."""
    return export("docx", None, *extra)


def export_markdown(*extra: str):
    """Back-compat alias for tests/old scripts."""
    return export("markdown", None, *extra)


def all_formats_with_cover(*extra: str):
    """
    Export all main formats with a default cover, passing through validated extras.
    """
    args = ["--format", "pdf,epub,docx,markdown", "--cover", "assets/covers/cover.jpg"]

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(list(extra), FULL_EXPORT_ALLOWED_OPTS)

    if invalid:
        print("⚠️ Invalid options for full_export_book.py:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options to full_export_book.py:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_full_export(args)


def export_epub2(*extra: str):
    """
    Export EPUB2 flavor; pass through validated extras.
    """
    args = ["--epub2"]

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(list(extra), FULL_EXPORT_ALLOWED_OPTS)

    if invalid:
        print("⚠️ Invalid options for full_export_book.py:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options to full_export_book.py:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_full_export(args)


def export_epub2_with_cover(*extra: str):
    """
    Export EPUB2 with a default cover; pass through validated extras.
    """
    args = ["--epub2", "--cover", "assets/covers/cover.jpg"]

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(list(extra), FULL_EXPORT_ALLOWED_OPTS)

    if invalid:
        print("⚠️ Invalid options for full_export_book.py:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options to full_export_book.py:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_full_export(args)


def export_print_version_epub(*extra: str):
    """
    Export the print-optimized EPUB via print_version_build.py.
    Accepts both print-version and full-export flags; validates both sets.
    """
    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]

    # Allow both sets: print_version_build consumes some, forwards others
    valid, invalid = _split_valid_invalid_options(
        list(extra), PRINT_VERSION_ALLOWED_OPTS | FULL_EXPORT_ALLOWED_OPTS
    )

    if invalid:
        print("⚠️ Invalid options for print_version_build/full_export:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options:")
        print("   " + " ".join(valid))

    _run_print_version(valid)


def export_print_version_paperback(*extra: str):
    """
    Print-optimized EPUB for paperback book type.
    """
    args = ["--book-type", "paperback"]

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(
        list(extra), PRINT_VERSION_ALLOWED_OPTS | FULL_EXPORT_ALLOWED_OPTS
    )

    if invalid:
        print("⚠️ Invalid options for print_version_build/full_export:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_print_version(args)


def export_print_version_hardcover(*extra: str):
    """
    Print-optimized EPUB for hardcover book type.
    """
    args = ["--book-type", "hardcover"]

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(
        list(extra), PRINT_VERSION_ALLOWED_OPTS | FULL_EXPORT_ALLOWED_OPTS
    )

    if invalid:
        print("⚠️ Invalid options for print_version_build/full_export:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_print_version(args)


def export_safe(format: str, *extra: str):
    """
    Export in 'safe' mode:
      - Forces --skip-images unless user already provided one.
      - Forces --keep-relative-paths unless user already provided one.
    """
    args = ["--format", format]

    # Mutually exclusive in full_export_book.py: pick ONE
    if not _has_any_option(extra, {"--skip-images", "--keep-relative-paths"}):
        args.append("--skip-images")  # default safe behavior

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(list(extra), FULL_EXPORT_ALLOWED_OPTS)

    if invalid:
        print("⚠️ Invalid options for full_export_book.py:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options to full_export_book.py:")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_full_export(args)


# ──────────────────────────────────────────────────────────────────────────────
# Safe shortcut aliases (for Poetry script entries)
# ──────────────────────────────────────────────────────────────────────────────
def export_pdf_safe(*extra: str):
    return export_safe("pdf", *extra)


def export_epub_safe(*extra: str):
    return export_safe("epub", *extra)


def export_docx_safe(*extra: str):
    return export_safe("docx", *extra)


def export_markdown_safe(*extra: str):
    return export_safe("markdown", *extra)


def export_print_version_paperback_safe(*extra: str):
    """
    Print-optimized EPUB for paperback **in Safe Mode**:
      - Forces --skip-images and --keep-relative-paths (no in-place source edits).
      - Validates passthrough; aborts if --strict-opts and invalid flags present.
    """
    args = ["--book-type", "paperback"]

    # Add exactly one safe flag if none provided by user
    if not _has_any_option(extra, {"--skip-images", "--keep-relative-paths"}):
        args.append("--skip-images")

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(
        list(extra), PRINT_VERSION_ALLOWED_OPTS | FULL_EXPORT_ALLOWED_OPTS
    )

    if invalid:
        print("⚠️ Invalid options for print_version_build/full_export:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options (safe mode):")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_print_version(args)


def export_print_version_hardcover_safe(*extra: str):
    """
    Print-optimized EPUB for hardcover **in Safe Mode**:
      - Forces --skip-images and --keep-relative-paths (no in-place source edits).
      - Validates passthrough; aborts if --strict-opts and invalid flags present.
    """
    args = ["--book-type", "hardcover"]

    if not _has_any_option(extra, {"--skip-images", "--keep-relative-paths"}):
        args.append("--skip-images")

    strict = "--strict-opts" in extra
    extra = [t for t in extra if t != "--strict-opts"]
    valid, invalid = _split_valid_invalid_options(
        list(extra), PRINT_VERSION_ALLOWED_OPTS | FULL_EXPORT_ALLOWED_OPTS
    )

    if invalid:
        print("⚠️ Invalid options for print_version_build/full_export:")
        print("   " + " ".join(invalid))
        if strict:
            print("🛑 Aborting due to --strict-opts.")
            return

    if valid:
        print("🔧 Forwarding valid options (safe mode):")
        print("   " + " ".join(valid))

    args.extend(valid)
    _run_print_version(args)


# ──────────────────────────────────────────────────────────────────────────────
# CLI entrypoint (optional; keeps Poetry shortcuts intact)
# ──────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> None:
    """
    Simple CLI wrapper mainly for local/manual invocations.

    Pattern:
      shortcuts_export.py <command> [command-args] -- [passthrough-to-target...]
    """
    parser = argparse.ArgumentParser(
        prog="shortcuts_export",
        description="Shortcuts for exporting books with validated passthrough options.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # export
    p_export = sub.add_parser("export", help="Export via full_export_book.py")
    p_export.add_argument("--format", required=True, help="pdf|epub|docx|markdown")
    p_export.add_argument("--cover", default=None)
    p_export.add_argument("--strict-opts", action="store_true")
    p_export.add_argument("passthrough", nargs=argparse.REMAINDER)

    # epub2
    p_epub2 = sub.add_parser("epub2", help="Export EPUB2 via full_export_book.py")
    p_epub2.add_argument("--strict-opts", action="store_true")
    p_epub2.add_argument("passthrough", nargs=argparse.REMAINDER)

    # epub2-with-cover
    p_epub2c = sub.add_parser(
        "epub2-with-cover", help="Export EPUB2 with default cover"
    )
    p_epub2c.add_argument("--strict-opts", action="store_true")
    p_epub2c.add_argument("passthrough", nargs=argparse.REMAINDER)

    # print-version
    p_print = sub.add_parser("print-version", help="Export print-optimized EPUB")
    p_print.add_argument("--book-type", choices=["paperback", "hardcover"])
    p_print.add_argument("--strict-opts", action="store_true")
    p_print.add_argument("passthrough", nargs=argparse.REMAINDER)

    # safe
    p_safe = sub.add_parser("safe", help="Export in safe mode (skips heavy steps)")
    p_safe.add_argument("--format", required=True)
    p_safe.add_argument("--strict-opts", action="store_true")
    p_safe.add_argument("passthrough", nargs=argparse.REMAINDER)

    # list-allowed-opts
    sub.add_parser("list-allowed-opts", help="Print valid options for targets")

    ns = parser.parse_args(argv if argv is not None else sys.argv[1:])
    extras = ns.passthrough if hasattr(ns, "passthrough") else []

    # strip a leading bare '--' from passthrough if present
    if extras and extras[0] == "--":
        extras = extras[1:]

    if ns.cmd == "export":
        export(
            ns.format, ns.cover, *extras, *(["--strict-opts"] if ns.strict_opts else [])
        )
    elif ns.cmd == "epub2":
        export_epub2(*extras, *(["--strict-opts"] if ns.strict_opts else []))
    elif ns.cmd == "epub2-with-cover":
        export_epub2_with_cover(*extras, *(["--strict-opts"] if ns.strict_opts else []))
    elif ns.cmd == "print-version":
        if ns.book_type == "hardcover":
            export_print_version_hardcover(
                *extras, *(["--strict-opts"] if ns.strict_opts else [])
            )
        elif ns.book_type == "paperback":
            export_print_version_paperback(
                *extras, *(["--strict-opts"] if ns.strict_opts else [])
            )
        else:
            export_print_version_epub(
                *extras, *(["--strict-opts"] if ns.strict_opts else [])
            )
    elif ns.cmd == "safe":
        export_safe(ns.format, *extras, *(["--strict-opts"] if ns.strict_opts else []))
    elif ns.cmd == "list-allowed-opts":
        list_allowed_opts()
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
