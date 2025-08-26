from __future__ import annotations
from pathlib import Path
import subprocess

from .paths import ProjectPaths
from .metadata import get_project_name, get_metadata_lang, get_or_create_metadata_file
from .fsops import prepare_output_folder
from .toc import normalize_toc
from .images import pre_image_steps, post_image_steps
from .pandoc_cmd import FORMATS, resolve_ext, collect_md_files, build_pandoc_cmd
from .validators import schedule_validations

DEFAULT_SECTION_ORDER = [
    "front-matter/toc.md",
    "front-matter/preface.md",
    "front-matter/introduction.md",
    "front-matter/foreword.md",
    "chapters",
    "back-matter/epilogue.md",
    "back-matter/glossary.md",
    "back-matter/appendix.md",
    "back-matter/acknowledgments.md",
    "back-matter/about-the-author.md",
    "back-matter/faq.md",
    "back-matter/bibliography.md",
    "back-matter/index.md",
]

def derive_output_basename(project_name: str, cli_name: str|None, preset: str|None, book_type: str) -> str:
    if cli_name: return f"{cli_name}-{book_type}"
    if preset is None: return f"{project_name}-{book_type}"
    return f"{preset}-{book_type}"

def build_one(fmt: str, paths: ProjectPaths, output_basename: str, section_order: list[str],
              cover: Path|None, force_epub2: bool, lang: str|None, custom_md_ext: str|None, log_file: Path|None):
    ext = resolve_ext(fmt, custom_md_ext)
    out_path = paths.output_dir / f"{output_basename}.{ext}"
    md_files = collect_md_files(paths.book_dir, section_order)
    if not md_files:
        print(f"❌ No Markdown files found for format {fmt}. Skipping."); return
    cmd = build_pandoc_cmd(fmt, out_path, md_files, paths.assets_dir, paths.metadata_file, lang, force_epub2, cover, custom_md_ext)
    with open(log_file, "a") if log_file else open("/dev/null","w") as log:
        subprocess.run(cmd, check=True, stdout=log, stderr=log)
    print(f"✅ Successfully generated: {out_path}")

def build_all(root: Path,
              formats: list[str] | None,
              section_order: list[str],
              book_type: str,
              output_file_cli: str|None,
              output_file_preset: str|None,
              lang_cli: str|None,
              custom_md_ext: str|None,
              cover_path: Path|None,
              epub2: bool,
              skip_images: bool,
              keep_relative: bool,
              log_file: Path):
    paths = ProjectPaths(root)

    # Resolve metadata and language
    project_name = get_project_name(paths.pyproject)
    paths.metadata_file, is_temp_metadata = get_or_create_metadata_file(paths.metadata_file)
    try:
        lang = lang_cli or get_metadata_lang(paths.metadata_file) or "en"

        # TOC
        normalize_toc(paths.toc_file, paths.normalizer, ext=(custom_md_ext or "md"), mode="strip-to-anchors", log_file=log_file)

        # Pre steps
        pre_image_steps(paths.conv_abs, paths.img_script, skip_images, keep_relative, log_file)

        # FS prep
        prepare_output_folder(paths.output_dir, paths.backup_dir)

        # Output base name
        output_basename = derive_output_basename(project_name, output_file_cli, output_file_preset, book_type)
        print(f"📘 Output file base name set to: {output_basename}")
        print(f"🌐 Using language: '{lang}'")

        # Formats
        selected = formats or list(FORMATS.keys())
        for fmt in selected:
            if fmt in FORMATS:
                build_one(fmt, paths, output_basename, section_order, cover_path, epub2, lang, custom_md_ext, log_file)
            else:
                print(f"⚠️ Skipping unknown format: {fmt}")

        # Post steps
        post_image_steps(paths.conv_rel, paths.img_script, skip_images, keep_relative, log_file)

        # Validations (non-blocking)
        schedule_validations(selected, output_basename, paths.output_dir, resolve_ext)

        print("\n🚀 Export completed. Background validation in progress...")
        print(f"📁 Outputs: {paths.output_dir}")
        print(f"📄 Logs: {log_file}")

    finally:
        if is_temp_metadata:
            try:
                paths.metadata_file.unlink(missing_ok=True)
                print(f"🗑️ Deleted temporary metadata file: {paths.metadata_file}")
            except OSError as e:
                print(f"⚠️ Could not delete temporary metadata file {paths.metadata_file}: {e}")
