import os
import subprocess

def validate_epub_with_epubcheck(epub_path):
    """
    Validates EPUB file. Prints result directly (no queue needed for fire-and-forget).
    """
    if not os.path.exists(epub_path):
        print(f"❌ EPUB file not found for validation: {epub_path}")
        return

    try:
        result = subprocess.run(
            ["epubcheck", epub_path],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Optional: add timeout in case epubcheck hangs
            timeout=60
        )

        if result.returncode == 0:
            print(f"✅ epubcheck: {epub_path} is valid! 🎉")
        else:
            print(f"❌ epubcheck found issues in: {epub_path}")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            print("🔧 Consider fixing the above issues.")

    except FileNotFoundError:
        print("⚠️  epubcheck not found. Install it (`brew install epubcheck`, `apt install epubcheck`) to validate EPUBs.")
    except subprocess.TimeoutExpired:
        print(f"⏰ epubcheck timed out while checking {epub_path}.")
    except Exception as e:
        print(f"⚠️  Unexpected error during epubcheck: {e}")


def validate_pdf(pdf_path):
    """Check if PDF is readable using `pdfinfo` (from poppler)."""
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            pages_line = [line for line in result.stdout.splitlines() if "Pages:" in line]
            page_count = pages_line[0] if pages_line else ""
            print(f"✅ PDF is valid: {pdf_path} {page_count}")
        else:
            print(f"❌ pdfinfo failed on {pdf_path}: {result.stderr}")
    except FileNotFoundError:
        print("🔍 PDF generated, but `pdfinfo` not found (install poppler to validate).")
    except Exception as e:
        print(f"⚠️  Error validating PDF: {e}")


def validate_docx(docx_path):
    """Try to open DOCX to verify integrity (lightweight)."""
    if not os.path.exists(docx_path):
        print(f"❌ DOCX file not found: {docx_path}")
        return

    try:
        import zipfile
        with zipfile.ZipFile(docx_path) as z:
            if "[Content_Types].xml" in z.namelist():
                print(f"✅ DOCX is valid: {docx_path}")
            else:
                print(f"❌ Invalid DOCX: missing core file in {docx_path}")
    except Exception as e:
        print(f"❌ DOCX appears corrupted: {docx_path} — {e}")


def validate_markdown(md_path):
    """Optional: check if markdown file exists and is non-empty."""
    if not os.path.exists(md_path):
        print(f"❌ Markdown file not found: {md_path}")
        return

    try:
        size = os.path.getsize(md_path)
        if size > 0:
            print(f"✅ Markdown exported: {md_path} ({size} bytes)")
        else:
            print(f"⚠️  Markdown file is empty: {md_path}")
    except Exception as e:
        print(f"⚠️  Error checking markdown: {e}")
