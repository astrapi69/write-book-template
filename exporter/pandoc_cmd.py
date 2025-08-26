from __future__ import annotations
from pathlib import Path

FORMATS = {"markdown": "gfm", "pdf": "pdf", "epub": "epub", "docx": "docx"}

def resolve_ext(fmt: str, custom_md_ext: str|None) -> str:
    return custom_md_ext if fmt=="markdown" and custom_md_ext else FORMATS[fmt]

def collect_md_files(book_dir: Path, section_order: list[str]) -> list[Path]:
    out: list[Path] = []
    for section in section_order:
        p = (book_dir / section)
        if p.is_dir():
            out.extend(sorted([x for x in p.iterdir() if x.suffix==".md"]))
        elif p.is_file():
            out.append(p)
    return out

def build_pandoc_cmd(fmt: str, out_path: Path, md_files: list[Path], assets_dir: Path, metadata_file: Path,
                     lang: str|None, force_epub2: bool, cover_path: Path|None, custom_md_ext: str|None):
    to_fmt = FORMATS[fmt]
    cmd = [
        "pandoc", "--verbose", "--from=markdown",
        f"--to={to_fmt}",
        f"--output={str(out_path)}",
        f"--resource-path={str(assets_dir.resolve())}",
        f"--metadata-file={str(metadata_file)}",
        *[str(p) for p in md_files],
    ]
    if fmt=="epub":
        if lang: cmd += ["--metadata", f"lang={lang}"]
        if force_epub2: cmd += ["--metadata", "epub.version=2"]
        if cover_path: cmd += [f"--epub-cover-image={str(cover_path)}"]
    if fmt=="pdf":
        cmd += ["--pdf-engine=lualatex", "-V", "mainfont=DejaVu Sans", "-V", "monofont=DejaVu Sans Mono"]
    if fmt=="markdown":
        cmd += ["--wrap=none"]
    return cmd
