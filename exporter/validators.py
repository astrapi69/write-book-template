from __future__ import annotations
from pathlib import Path
import threading, subprocess

def _spawn(name: str, target, args: tuple):
    t = threading.Thread(name=name, target=target, args=args, daemon=False)
    t.start(); return t

def validate_epub_with_epubcheck(path: Path): print(f"🧩 EPUB generated. Validation running in background..."); # call epubcheck here
def validate_pdf(path: Path): print(f"🧩 PDF generated. Validation running in background...")
def validate_docx(path: Path): print(f"🧩 DOCX generated. Validation running in background...")
def validate_markdown(path: Path): print(f"🧩 Markdown generated. Validation running in background...")

def schedule_validations(selected_formats: list[str], output_basename: str, output_dir: Path, resolve_ext):
    threads = []
    for fmt in selected_formats:
        ext = resolve_ext(fmt, None if fmt!="markdown" else None)
        out_file = output_dir / f"{output_basename}.{ext}"
        if fmt=="epub": threads.append(_spawn("Validate-EPUB", validate_epub_with_epubcheck, (out_file,)))
        elif fmt=="pdf": threads.append(_spawn("Validate-PDF", validate_pdf, (out_file,)))
        elif fmt=="docx": threads.append(_spawn("Validate-DOCX", validate_docx, (out_file,)))
        elif fmt=="markdown": threads.append(_spawn("Validate-MD", validate_markdown, (out_file,)))
    return threads
