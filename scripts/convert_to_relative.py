#!/usr/bin/env python3
# scripts/convert_to_relative.py
import os
import re
from pathlib import Path
from typing import Tuple

# --- Project layout ----------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"
ASSETS_DIR = PROJECT_ROOT / "assets"

MD_DIRECTORIES = [
    MANUSCRIPT_DIR / "chapters",
    MANUSCRIPT_DIR / "front-matter",
    MANUSCRIPT_DIR / "back-matter",
]

# --- Patterns ---------------------------------------------------------------
# Markdown links/images:    ![alt](target "title")   [text](target "title")
MD_LINK_RE = re.compile(
    r"""
    (?P<prefix>!?\[[^\]]*\]\()         # opening [..]( or ![..](
    \s*
    (?P<target><[^>]*>|[^)]+?)   # target: <...> or anything (spaces allowed), lazy
    (?P<title>\s+["'][^)]*["']\s*)?    # optional title
    \)                                 # closing
    """,
    re.VERBOSE,
)

# HTML img/src and a/href
IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=)(["\'])([^"\']+)\2', re.IGNORECASE)
A_HREF_RE = re.compile(r'(<a\b[^>]*?\bhref=)(["\'])([^"\']+)\2', re.IGNORECASE)

SCHEME_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9+\-.]*:"
)  # http:, https:, mailto:, data:, etc.


def _strip_angles(s: str) -> Tuple[str, bool]:
    return (s[1:-1], True) if s.startswith("<") and s.endswith(">") else (s, False)


def _is_absolute_path(p: str) -> bool:
    try:
        return Path(p).is_absolute() or p.startswith("/")
    except Exception:
        return False


def _is_url_or_anchor(t: str) -> bool:
    return not t or t.startswith("#") or SCHEME_RE.match(t) is not None


def _inside_assets(abs_path: Path) -> bool:
    try:
        abs_path.resolve().relative_to(ASSETS_DIR.resolve())
        return True
    except Exception:
        return False


def convert_target_to_relative(raw_target: str, file_dir: Path) -> str:
    """
    Convert a single link/image target back to relative if:
    - it's an absolute filesystem path,
    - and it points inside the project's assets directory.
    Angle brackets are preserved if present.
    """
    target, had_angles = _strip_angles(raw_target.strip())

    if _is_url_or_anchor(target) or not _is_absolute_path(target):
        return raw_target

    abs_path = Path(target)
    if not _inside_assets(abs_path):
        return raw_target

    try:
        rel_str = os.path.relpath(abs_path.resolve(), start=file_dir.resolve())
    except Exception:
        return raw_target
    # Normalize separators for Markdown
    rel_str = Path(rel_str).as_posix()

    return f"<{rel_str}>" if had_angles else rel_str


def convert_paths_in_text(text: str, file_path: Path) -> str:
    file_dir = file_path.parent

    def md_repl(m: re.Match) -> str:
        new_target = convert_target_to_relative(m.group("target"), file_dir)
        return f'{m.group("prefix")}{new_target}{m.group("title") or ""})'

    def html_repl(m: re.Match) -> str:
        prefix, quote, target = m.group(1), m.group(2), m.group(3)
        new_target = convert_target_to_relative(target, file_dir)
        return f"{prefix}{quote}{new_target}{quote}"

    text = MD_LINK_RE.sub(md_repl, text)
    text = IMG_SRC_RE.sub(html_repl, text)
    text = A_HREF_RE.sub(html_repl, text)
    return text


def process_md_file(md_file: Path) -> bool:
    original = md_file.read_text(encoding="utf-8")
    converted = convert_paths_in_text(original, md_file)
    if converted != original:
        md_file.write_text(converted, encoding="utf-8")
        print(f"🔁 Converted to relative: {md_file}")
        return True
    return False


def main() -> None:
    changed = 0
    for md_dir in MD_DIRECTORIES:
        if not md_dir.exists():
            continue
        for md_file in md_dir.rglob("*.md"):
            changed += 1 if process_md_file(md_file) else 0
    print("🔄 All Markdown files reverted to relative paths.")
    print(f"✅ Files updated: {changed}")


if __name__ == "__main__":
    main()
