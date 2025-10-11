#!/usr/bin/env python3
# scripts/validate_format.py
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional

DEFAULT_EPUBCHECK_TIMEOUT = 60
DEFAULT_PDFINFO_TIMEOUT = 30


def run_cmd(cmd: list[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Run a command and return (rc, stdout, stderr). Never raises."""
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", f"unexpected error: {e}"


def require_cmd(name: str) -> bool:
    """Return True if binary is available in PATH, else False."""
    return shutil.which(name) is not None


# --- Validators ---------------------------------------------------------------


def validate_epub_with_epubcheck(
    epub_path: str, timeout: int = DEFAULT_EPUBCHECK_TIMEOUT
) -> int:
    """
    Validate EPUB using epubcheck. Prints result and returns exit code:
      0 = valid / success
      1 = issues / generic failure
      2 = input not found
      127 = epubcheck missing
      124 = timeout
    """
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found for validation: {epub_path}")
        return 2

    if not require_cmd("epubcheck"):
        print(
            "⚠️  epubcheck not found. Install it (`brew install epubcheck`, `apt install epubcheck`) to validate EPUBs."
        )
        return 127

    rc, out, err = run_cmd(["epubcheck", epub_path], timeout=timeout)

    if rc == 0:
        print(f"✅ epubcheck: {epub_path} is valid! 🎉")
        return 0
    if rc == 124:
        print(f"⏰ epubcheck timed out while checking {epub_path}.")
        return 124
    if rc == 127:
        print(
            "⚠️  epubcheck not found. Install it (`brew install epubcheck`, `apt install epubcheck`)."
        )
        return 127

    print(f"❌ epubcheck found issues in: {epub_path}")
    if out.strip():
        print(out.strip())
    if err.strip():
        print(err.strip())
    print("🔧 Consider fixing the above issues.")
    return 1


def validate_pdf(pdf_path: str, timeout: int = DEFAULT_PDFINFO_TIMEOUT) -> int:
    """
    Validate/read PDF metadata with pdfinfo (Poppler). Returns:
      0 = valid
      1 = pdfinfo reported error
      2 = input not found
      127 = pdfinfo missing
      124 = timeout
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return 2

    if not require_cmd("pdfinfo"):
        print(
            "🔍 PDF generated, but `pdfinfo` not found (install poppler to validate)."
        )
        return 127

    rc, out, err = run_cmd(["pdfinfo", pdf_path], timeout=timeout)
    if rc == 0:
        page_line = next((ln for ln in out.splitlines() if ln.startswith("Pages:")), "")
        extra = f" {page_line}".rstrip() if page_line else ""
        print(f"✅ PDF is valid: {pdf_path}{extra}")
        return 0
    if rc == 124:
        print(f"⏰ pdfinfo timed out while checking {pdf_path}.")
        return 124
    print(f"❌ pdfinfo failed on {pdf_path}: {err.strip() or 'unknown error'}")
    return 1


def validate_docx(docx_path: str) -> int:
    """
    Lightweight DOCX integrity check via ZIP structure.
      0 = looks valid
      1 = corrupted/invalid
      2 = input not found
    """
    if not os.path.exists(docx_path):
        print(f"❌ DOCX file not found: {docx_path}")
        return 2

    try:
        import zipfile

        with zipfile.ZipFile(docx_path) as zf:
            if "[Content_Types].xml" in zf.namelist():
                print(f"✅ DOCX is valid: {docx_path}")
                return 0
            print(f"❌ Invalid DOCX: missing core file in {docx_path}")
            return 1
    except Exception as e:
        print(f"❌ DOCX appears corrupted: {docx_path} — {e}")
        return 1


def validate_markdown(md_path: str) -> int:
    """
    Basic Markdown output check:
      0 = exists and non-empty
      1 = empty
      2 = input not found
    """
    if not os.path.exists(md_path):
        print(f"❌ Markdown file not found: {md_path}")
        return 2
    try:
        size = os.path.getsize(md_path)
        if size > 0:
            print(f"✅ Markdown exported: {md_path} ({size} bytes)")
            return 0
        print(f"⚠️  Markdown file is empty: {md_path}")
        return 1
    except Exception as e:
        print(f"⚠️  Error checking markdown: {e}")
        return 1


# --- CLI ---------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate exported book formats (EPUB, PDF, DOCX, Markdown)."
    )
    p.add_argument("path", help="Path to the file to validate.")
    p.add_argument(
        "--type",
        choices=["epub", "pdf", "docx", "md"],
        help="Force a specific validator (otherwise auto-detect by extension).",
    )
    p.add_argument("--epub-timeout", type=int, default=DEFAULT_EPUBCHECK_TIMEOUT)
    p.add_argument("--pdf-timeout", type=int, default=DEFAULT_PDFINFO_TIMEOUT)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = args.path
    kind = (args.type or Path(path).suffix.lower().lstrip(".")).lower()

    if kind == "epub":
        rc = validate_epub_with_epubcheck(path, timeout=args.epub_timeout)
    elif kind == "pdf":
        rc = validate_pdf(path, timeout=args.pdf_timeout)
    elif kind == "docx":
        rc = validate_docx(path)
    elif kind in {"md", "markdown"}:
        rc = validate_markdown(path)
    else:
        print(
            f"⚠️  Unknown type for '{path}'. Use --type to specify one of: epub, pdf, docx, md"
        )
        rc = 1

    import sys

    sys.exit(rc)


if __name__ == "__main__":
    raise SystemExit(main())
