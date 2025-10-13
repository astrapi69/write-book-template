# scripts/inject_images.py
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

# ---- Helpers for prompt loading ----


def _flatten_prompts(data: dict) -> List[dict]:
    """
    Accepts either:
      - {"prompts": [ {...}, {...} ]}
      - {"chapters": [{"prompts":[{...}, ...]}, ...], "style": "..."}
    Returns a flat list of prompt items (dicts).
    """
    if not isinstance(data, dict):
        return []
    if "prompts" in data and isinstance(data["prompts"], list):
        return data["prompts"]
    acc: List[dict] = []
    for ch in data.get("chapters", []):
        if isinstance(ch, dict):
            for p in ch.get("prompts", []):
                if isinstance(p, dict):
                    acc.append(p)
    return acc


def load_prompts(prompt_file: Path) -> List[dict]:
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    try:
        with prompt_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {prompt_file}: {e}") from e

    prompts = _flatten_prompts(data)
    if not prompts:
        raise ValueError(
            "Prompt JSON must contain a list of prompt objects under 'prompts' or 'chapters[].prompts'."
        )
    # Keep only entries that have filename
    return [p for p in prompts if isinstance(p, dict) and p.get("filename")]


# ---- Mapping chapter <-> filename ----

_CHAPTER_NUM_RE = re.compile(r"(?:^|[_\-])(?:chapter[_\-]?)?(\d{1,2})(?!\d)")


def _extract_two_digit(num_str: str) -> str:
    try:
        n = int(num_str)
        return f"{n:02d}"
    except Exception:
        return ""


def chapter_key_from_filename(filename: str) -> str:
    """
    Extract a canonical 2-digit chapter key from a filename like:
     - '01-intro.png'     -> '01'
     - 'chapter_2-cover'  -> '02'
     - '03.png'           -> '03'
    Returns '' if no match.
    """
    stem = Path(filename).stem.lower()
    # look for number in typical patterns
    m = _CHAPTER_NUM_RE.search(stem)
    if m:
        return _extract_two_digit(m.group(1))
    # fallback: plain leading digits
    m2 = re.match(r"^(\d{1,2})", stem)
    if m2:
        return _extract_two_digit(m2.group(1))
    return ""


def chapter_key_from_chapterfile(chapter_path: Path) -> str:
    stem = chapter_path.stem.lower()
    # Expect names like '01-intro.md' or similar
    m = re.match(r"^(\d{1,2})", stem)
    if m:
        return _extract_two_digit(m.group(1))
    # Try 'chapter_01-...' too
    m2 = _CHAPTER_NUM_RE.search(stem)
    if m2:
        return _extract_two_digit(m2.group(1))
    return ""


def build_filename_map(prompts: Iterable[dict]) -> Dict[str, str]:
    """
    Map canonical chapter key ('01', '02', ...) -> image filename
    Last one wins if multiple prompts map to same chapter key.
    """
    mapping: Dict[str, str] = {}
    for p in prompts:
        filename = str(p.get("filename", "")).strip()
        if not filename:
            continue
        key = chapter_key_from_filename(filename)
        if key:
            mapping[key] = filename
    return mapping


# ---- Injection logic ----

_IMG_BY_BASENAME_RE_TEMPLATE = r"!\[[^\]]*\]\((?P<path>[^)]*[/\\])?%s\)"


def link_already_present(content: str, image_filename: str) -> bool:
    """
    Detect any Markdown image whose URL ends with the same basename
    (alt text and directory prefixes may vary).
    """
    pattern = _IMG_BY_BASENAME_RE_TEMPLATE % re.escape(Path(image_filename).name)
    return re.search(pattern, content, flags=re.IGNORECASE) is not None


def compute_relative_image_path(chapter_file: Path, image_full_path: Path) -> str:
    rel = os.path.relpath(image_full_path, start=chapter_file.parent)
    return Path(rel).as_posix()


def find_insertion_index(lines: List[str]) -> int:
    """
    Insert after the first H1 ('# ') if present; otherwise at the top
    (after YAML front matter if detected).
    """
    # Handle YAML front matter
    if lines and lines[0].strip() == "---":
        # find closing '---'
        for i in range(1, min(len(lines), 200)):  # small cap
            if lines[i].strip() == "---":
                # Insert after front matter block
                return i + 1

    # find first H1
    for i, line in enumerate(lines):
        if line.lstrip().startswith("# "):
            return i + 1

    # default: top
    return 0


def inject_image(
    content: str, image_rel_path: str, alt_text: Optional[str] = None
) -> tuple[str, bool]:
    """
    Insert a Markdown image and return (new_content, injected_flag).
    If a link to the same basename already exists, return (content, False).
    """
    image_filename = Path(image_rel_path).name
    if link_already_present(content, image_filename):
        return content, False

    alt = (alt_text or Path(image_filename).stem or "image").strip()
    lines = content.splitlines()
    idx = find_insertion_index(lines)

    # If inserting at the very top, no leading blank line.
    md_line = (
        f"![{alt}]({image_rel_path})\n"
        if idx == 0
        else f"\n![{alt}]({image_rel_path})\n"
    )

    lines.insert(idx, md_line)
    new_content = "\n".join(lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    return new_content, True


# ---- Runner ----


@dataclass
class Stats:
    total: int = 0
    injected: int = 0
    skipped_existing: int = 0
    missing_prompt: int = 0
    missing_image: int = 0


def process(
    chapter_dir: Path,
    image_dir: Path,
    prompt_file: Path,
    dry_run: bool = False,
) -> Stats:
    prompts = load_prompts(prompt_file)
    filename_map = build_filename_map(prompts)
    chapter_files = sorted(chapter_dir.glob("*.md"))

    stats = Stats(total=len(chapter_files))

    for chapter_file in chapter_files:
        key = chapter_key_from_chapterfile(chapter_file)
        image_name = filename_map.get(key)
        if not image_name:
            print(f"⚠️ No image defined for: {chapter_file.name} (key: {key})")
            stats.missing_prompt += 1
            continue

        image_full = image_dir / image_name
        if not image_full.exists():
            print(f"⚠️ Image not found: {image_full}")
            stats.missing_image += 1
            continue

        content = chapter_file.read_text(encoding="utf-8")
        rel_path = compute_relative_image_path(chapter_file, image_full)
        new_content, injected = inject_image(content, rel_path)

        if not injected:
            print(f"ℹ️ Already contains image: {chapter_file.name}")
            stats.skipped_existing += 1
            continue

        if dry_run:
            print(f"🔍 Dry-run: would inject image into {chapter_file.name}")
        else:
            chapter_file.write_text(new_content, encoding="utf-8")
            print(f"✅ Image injected into: {chapter_file.name}")

        stats.injected += 1

    print("\n📊 Summary")
    print("----------")
    print(f"📄 Total chapters processed: {stats.total}")
    print(f"✅ Images injected:          {stats.injected}")
    print(f"ℹ️ Already had image:       {stats.skipped_existing}")
    print(f"❌ No prompt match:         {stats.missing_prompt}")
    print(f"❌ Missing image file:      {stats.missing_image}")

    return stats


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Inject generated images into chapter markdown files"
    )
    p.add_argument(
        "--chapter-dir",
        default="manuscript/chapters",
        type=Path,
        help="Directory with chapter .md files",
    )
    p.add_argument(
        "--image-dir",
        default="assets/illustrations",
        type=Path,
        help="Directory with generated images",
    )
    p.add_argument(
        "--prompt-file",
        default="scripts/data/image_prompts.json",
        type=Path,
        help="Prompt JSON path",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Run without writing changes to files"
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(list(argv) if argv is not None else None)
    try:
        _ = process(
            args.chapter_dir, args.image_dir, args.prompt_file, dry_run=args.dry_run
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        return 2
    # Non-zero on partial failure can be useful; keep 0 for now to match original behavior.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
