# scripts/create_chapters.py
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, List, Optional

LOG = logging.getLogger("create_chapters")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def _detect_next_start(chapter_dir: Path) -> int:
    """
    Inspect `chapter_dir` for files like 'NN-chapter.md' and return the next integer.
    If none exist, return 1.
    """
    existing_nums: List[int] = []
    for p in chapter_dir.glob("[0-9][0-9]-chapter.md"):
        try:
            existing_nums.append(int(p.stem.split("-")[0]))
        except ValueError:
            # Ignore unexpected filenames
            continue
    return (max(existing_nums) + 1) if existing_nums else 1


def create_chapter_files(
    project_dir: Optional[str | Path],
    total: int,
    start: Optional[int] = None,
    *,
    dry_run: bool = False,
) -> List[Path]:
    """
    Create chapter markdown files named 'NN-chapter.md' under
    <project>/manuscript/chapters.

    Args:
        project_dir: Project root. If None or empty, uses current working directory.
        total: How many chapter files to create (must be >= 1).
        start: Optional starting chapter number. If None, continues after the
               highest existing chapter in the target directory (or 1 if none).
        dry_run: If True, do not write to disk; just return the would-be file paths.

    Returns:
        List of file paths that were created (or would be created in dry-run).

    Raises:
        ValueError: If `total` < 1 or `start` is invalid (< 1).
    """
    if total < 1:
        raise ValueError("`total` must be >= 1.")
    if start is not None and start < 1:
        raise ValueError("`start` must be >= 1 when provided.")

    root = Path(project_dir) if project_dir and str(project_dir).strip() else Path.cwd()
    chapter_dir = root / "manuscript" / "chapters"
    if not dry_run:
        chapter_dir.mkdir(parents=True, exist_ok=True)

    start_num = start if start is not None else _detect_next_start(chapter_dir)
    end_num = start_num + total - 1

    planned: List[Path] = []
    for i in range(start_num, end_num + 1):
        filename = f"{i:02d}-chapter.md"
        path = chapter_dir / filename
        planned.append(path)

    if dry_run:
        for p in planned:
            LOG.info(f"[dry-run] Would create: {p}")
        return planned

    created: List[Path] = []
    for p in planned:
        # `touch(exist_ok=True)` won't overwrite contents if file exists (safe)
        p.touch(exist_ok=True)
        LOG.info(f"✓ Created: {p}")
        created.append(p)

    return created


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate chapter Markdown files.")
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
        help="Number of chapters to create (>= 1).",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Optional starting chapter number (>= 1). If omitted, continues after the last existing chapter.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only; show what would be created without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        create_chapter_files(
            project_dir=args.project_dir,
            total=args.total,
            start=args.start,
            dry_run=args.dry_run,
        )
    except ValueError as e:
        LOG.error(f"Error: {e}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
