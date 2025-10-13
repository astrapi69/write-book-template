# scripts/create_chapters.py
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import List, Optional, Sequence

LOG = logging.getLogger("create_chapters")
logging.basicConfig(level=logging.INFO, format="%(message)s")

DEFAULT_PATTERN = "{num:02d}-chapter.md"


def _ensure_valid_pattern(pattern: str) -> None:
    """
    Validate that the pattern contains a '{num' placeholder.
    """
    if "{num" not in pattern:
        raise ValueError(
            "`--name-pattern` must include a '{num}' placeholder (e.g. '{num:02d}-chapter.md')."
        )


def _pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """
    Convert a filename pattern (e.g. '{num:02d}-chapter.md') into a regex that
    captures the number as a named group 'num'.

    Rules:
    - '{num}' or '{num:...}' -> r'(?P<num>\\d+)'
    - All other characters are escaped
    """
    # Replace the {num...} token with placeholder, escape the rest, then put the group back in
    token_re = re.compile(r"\{num(?::[^}]*)?\}")
    if not token_re.search(pattern):
        raise ValueError("Pattern must contain a '{num}' placeholder.")

    parts = []
    last = 0
    for m in token_re.finditer(pattern):
        # Escape text before token
        if m.start() > last:
            parts.append(re.escape(pattern[last : m.start()]))
        # Insert capture group
        parts.append(r"(?P<num>\d+)")
        last = m.end()
    # Escape tail
    if last < len(pattern):
        parts.append(re.escape(pattern[last:]))

    regex = "^" + "".join(parts) + "$"
    return re.compile(regex)


def _detect_next_start(chapter_dir: Path, name_pattern: str) -> int:
    """
    Inspect `chapter_dir` for files matching the `name_pattern` and return next integer.
    If none exist, return 1.
    """
    rx = _pattern_to_regex(name_pattern)
    existing_nums: List[int] = []
    # We can't glob with a regex, so we list directory and match
    if not chapter_dir.exists():
        return 1
    for p in chapter_dir.iterdir():
        if not p.is_file():
            continue
        m = rx.match(p.name)
        if m:
            try:
                existing_nums.append(int(m.group("num")))
            except (KeyError, ValueError):
                continue
    return (max(existing_nums) + 1) if existing_nums else 1


def create_chapter_files(
    project_dir: Optional[str | Path],
    total: int,
    start: Optional[int] = None,
    *,
    dry_run: bool = False,
    name_pattern: str = DEFAULT_PATTERN,
) -> List[Path]:
    """
    Create files using a flexible name pattern, e.g. '{num:02d}-scene.md'.

    Args:
        project_dir: Project root. If None or empty, uses current working directory.
        total: How many files to create (>= 1).
        start: Starting number (>= 1). If None, continues after highest existing file.
        dry_run: If True, plan only (no disk writes).
        name_pattern: Filename pattern containing '{num}' placeholder.

    Returns:
        List of created (or planned) file paths.

    Raises:
        ValueError: On invalid `total`, `start`, or `name_pattern`.
    """
    if total < 1:
        raise ValueError("`total` must be >= 1.")
    if start is not None and start < 1:
        raise ValueError("`start` must be >= 1 when provided.")
    _ensure_valid_pattern(name_pattern)

    root = Path(project_dir) if project_dir and str(project_dir).strip() else Path.cwd()
    chapter_dir = root / "manuscript" / "chapters"
    if not dry_run:
        chapter_dir.mkdir(parents=True, exist_ok=True)

    start_num = (
        start if start is not None else _detect_next_start(chapter_dir, name_pattern)
    )
    end_num = start_num + total - 1

    planned: List[Path] = []
    for i in range(start_num, end_num + 1):
        # Python's str.format supports {num} and {num:02d}
        filename = name_pattern.format(num=i)
        planned.append(chapter_dir / filename)

    if dry_run:
        for p in planned:
            LOG.info(f"[dry-run] Would create: {p}")
        return planned

    created: List[Path] = []
    for p in planned:
        p.touch(exist_ok=True)
        LOG.info(f"✓ Created: {p}")
        created.append(p)

    return created


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Markdown files (chapters/scenes/parts) with a flexible name pattern."
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default="",
        help="Project root (default: current working directory).",
    )
    parser.add_argument(
        "--total",
        type=int,
        required=True,
        help="Number of files to create (>= 1).",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Optional starting number (>= 1). If omitted, continues after the last existing file matching the pattern.",
    )
    parser.add_argument(
        "--name-pattern",
        type=str,
        default=DEFAULT_PATTERN,
        help=f"Filename pattern with '{{num}}' placeholder (default: '{DEFAULT_PATTERN}'). "
        "Examples: '{num:02d}-chapter.md', '{num:03d}_scene.md', '{num}-part.md'",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only; show what would be created without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(list(argv) if argv is not None else None)
    try:
        create_chapter_files(
            project_dir=args.project_dir,
            total=args.total,
            start=args.start,
            dry_run=args.dry_run,
            name_pattern=args.name_pattern,
        )
    except ValueError as e:
        LOG.error(f"Error: {e}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
