#!/usr/bin/env python3
# scripts/fix_german_quotes.py
"""
fix_german_quotes.py - Converts quotation marks in Markdown files
to German typographic style.

Target format:
  Double: „ " (U+201E / U+201C)
  Single: ‚ ' (U+201A / U+2018)

Usage:
  python fix_german_quotes.py input.md
  python fix_german_quotes.py input.md --dry-run
  python fix_german_quotes.py ./my_book/           (recursive, *.md)
  python fix_german_quotes.py ./docs/ --pattern "*.markdown"
"""

import argparse
import re
import shutil
import sys
from pathlib import Path


# --- Character constants ---

# German target characters
DE_OPEN_DOUBLE = "\u201e"  # „
DE_CLOSE_DOUBLE = "\u201c"  # "
DE_OPEN_SINGLE = "\u201a"  # ‚
DE_CLOSE_SINGLE = "\u2018"  # '

# English typographic characters (to be replaced)
EN_OPEN_DOUBLE = "\u201c"  # " (identical to DE_CLOSE_DOUBLE)
EN_CLOSE_DOUBLE = "\u201d"  # "
EN_OPEN_SINGLE = "\u2018"  # ' (identical to DE_CLOSE_SINGLE)
EN_CLOSE_SINGLE = "\u2019"  # '

# Straight (ASCII) quotation marks
STRAIGHT_DOUBLE = '"'
STRAIGHT_SINGLE = "'"

# Default glob pattern for directory mode
DEFAULT_PATTERN = "*.md"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Converts quotation marks in Markdown files "
        "to German typographic style."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a Markdown file or directory (recursive).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing files.",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help=f"Glob pattern for directory mode (default: {DEFAULT_PATTERN}).",
    )
    return parser.parse_args()


def is_in_frontmatter(lines: list[str], line_idx: int) -> bool:
    """Check whether a line falls inside YAML frontmatter (--- ... ---)."""
    if not lines or not lines[0].rstrip() == "---":
        return False
    # Frontmatter starts at line 0, ends at the second ---
    fence_count = 0
    for i, line in enumerate(lines):
        if line.rstrip() == "---":
            fence_count += 1
        if fence_count == 2:
            return line_idx > 0 and line_idx <= i
    # No closing --- found, everything after the first --- is frontmatter
    return line_idx > 0


def mask_protected_regions(line: str) -> list[tuple[int, int]]:
    """
    Return a list of (start, end) ranges that must not be modified:
    inline code spans and HTML attribute values.
    """
    protected = []

    # Inline code: `...`
    for m in re.finditer(r"`[^`]+`", line):
        protected.append((m.start(), m.end()))

    # HTML attributes: key="..." or key='...'
    for m in re.finditer(r'(?:[\w-]+)\s*=\s*"[^"]*"', line):
        protected.append((m.start(), m.end()))
    for m in re.finditer(r"(?:[\w-]+)\s*=\s*'[^']*'", line):
        protected.append((m.start(), m.end()))

    return protected


def is_protected(pos: int, protected: list[tuple[int, int]]) -> bool:
    """Check whether a character position falls inside a protected region."""
    return any(start <= pos < end for start, end in protected)


def find_quote_positions(
    line: str, quote_char: str, protected: list[tuple[int, int]]
) -> list[int]:
    """Find all unprotected positions of a given character in the line."""
    positions = []
    for i, ch in enumerate(line):
        if ch == quote_char and not is_protected(i, protected):
            positions.append(i)
    return positions


def replace_straight_double_quotes(
    line: str,
    protected: list[tuple[int, int]],
    stats: dict,
    warnings: list,
    line_num: int,
) -> str:
    """
    Replace straight double quotation marks pairwise with German „ ".

    Also handles mixed cases: if a German opening „ (U+201E) is already
    present and a straight " follows as closing quote, only the closing
    character is converted.
    """
    chars = list(line)
    straight_positions = find_quote_positions(line, STRAIGHT_DOUBLE, protected)

    if not straight_positions:
        return line

    # Phase 1: Find existing German opening „ (U+201E) that expect
    # a straight " as their closing counterpart.
    orphan_openers = []
    for i, ch in enumerate(chars):
        if ch == DE_OPEN_DOUBLE and not is_protected(i, protected):
            orphan_openers.append(i)

    # Match each „ with the next following straight "
    consumed_straight = set()
    for opener_pos in orphan_openers:
        for sp in straight_positions:
            if sp > opener_pos and sp not in consumed_straight:
                chars[sp] = DE_CLOSE_DOUBLE
                consumed_straight.add(sp)
                stats["straight_double"] += 1
                break

    # Phase 2: Convert remaining straight " pairwise
    remaining = [p for p in straight_positions if p not in consumed_straight]

    if len(remaining) % 2 != 0:
        context = line.rstrip()
        warnings.append(
            f'Line {line_num}: Asymmetric straight quotation mark (") '
            f"- {len(remaining)} unpaired occurrence(s)\n"
            f"  Context: {context}"
        )
        stats["warnings"] += 1
        # Keep already converted characters
        return "".join(chars)

    for i in range(0, len(remaining), 2):
        open_pos = remaining[i]
        close_pos = remaining[i + 1]
        chars[close_pos] = DE_CLOSE_DOUBLE
        chars[open_pos] = DE_OPEN_DOUBLE
        stats["straight_double"] += 1

    return "".join(chars)


def replace_english_double_quotes(
    line: str, protected: list[tuple[int, int]], stats: dict
) -> str:
    """
    Replace English typographic double quotation marks with German ones.

    Only active when U+201D (EN_CLOSE_DOUBLE) is present.
    U+201C is ambiguous (= DE_CLOSE_DOUBLE), so it is only treated as
    EN_OPEN_DOUBLE when a matching U+201D follows.

    Strategy:
    - U+201C...U+201D pairs -> U+201E...U+201C (German)
    - Standalone U+201D -> U+201C
    """
    chars = list(line)

    # Only act when U+201D is present at all
    close_positions = []
    for i, ch in enumerate(chars):
        if ch == EN_CLOSE_DOUBLE and not is_protected(i, protected):
            close_positions.append(i)

    if not close_positions:
        return line

    # Find U+201C positions as potential openers
    open_positions = []
    for i, ch in enumerate(chars):
        if ch == EN_OPEN_DOUBLE and not is_protected(i, protected):
            open_positions.append(i)

    changed = False

    # Match pairs: U+201C followed by U+201D
    used_close = set()
    used_open = set()
    for op in open_positions:
        for ci, cp in enumerate(close_positions):
            if cp > op and ci not in used_close:
                # Pair found: U+201C -> U+201E, U+201D -> U+201C
                chars[op] = DE_OPEN_DOUBLE
                chars[cp] = DE_CLOSE_DOUBLE
                used_close.add(ci)
                used_open.add(open_positions.index(op))
                changed = True
                break

    # Convert remaining standalone U+201D to U+201C
    for ci, cp in enumerate(close_positions):
        if ci not in used_close:
            chars[cp] = DE_CLOSE_DOUBLE
            changed = True

    if changed:
        stats["english_double"] += 1

    return "".join(chars)


def replace_english_single_quotes(
    line: str, protected: list[tuple[int, int]], stats: dict
) -> str:
    """
    Replace English typographic single quotation marks with German ones.

    U+2018 (') -> DE_CLOSE_SINGLE (stays, is identical)
    U+2019 (') -> must be handled context-dependently.

    Strategy: U+2018...U+2019 pairs -> U+201A...U+2018 (German)
    """
    chars = list(line)

    open_positions = []
    close_positions = []
    for i, ch in enumerate(chars):
        if is_protected(i, protected):
            continue
        if ch == EN_OPEN_SINGLE:
            open_positions.append(i)
        elif ch == EN_CLOSE_SINGLE:
            close_positions.append(i)

    if not open_positions and not close_positions:
        return line

    # Match pairs: each U+2018 with the next U+2019
    changed = False
    used_close = set()
    for op in open_positions:
        for ci, cp in enumerate(close_positions):
            if cp > op and ci not in used_close:
                # Pair found
                chars[op] = DE_OPEN_SINGLE
                chars[cp] = DE_CLOSE_SINGLE
                used_close.add(ci)
                changed = True
                break

    if changed:
        stats["english_single"] += 1

    return "".join(chars)


def process_line(line: str, line_num: int, stats: dict, warnings: list) -> str:
    """Process a single line through all quote replacement stages."""
    protected = mask_protected_regions(line)

    # 1. Straight double quotation marks
    line = replace_straight_double_quotes(line, protected, stats, warnings, line_num)

    # Recompute protected regions after modification
    protected = mask_protected_regions(line)

    # 2. English typographic double quotation marks
    line = replace_english_double_quotes(line, protected, stats)

    protected = mask_protected_regions(line)

    # 3. English typographic single quotation marks
    line = replace_english_single_quotes(line, protected, stats)

    return line


def process_file(content: str, stats: dict, warnings: list) -> str:
    """Process the entire file content, respecting frontmatter and code blocks."""
    lines = content.split("\n")
    result_lines = []

    in_code_block = False
    in_frontmatter = False

    for line_num_0, line in enumerate(lines):
        line_num = line_num_0 + 1
        stripped = line.rstrip()

        # Frontmatter detection
        if line_num_0 == 0 and stripped == "---":
            in_frontmatter = True
            result_lines.append(line)
            continue

        if in_frontmatter and stripped == "---":
            in_frontmatter = False
            result_lines.append(line)
            continue

        if in_frontmatter:
            result_lines.append(line)
            continue

        # Fenced code block detection (```)
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue

        if in_code_block:
            result_lines.append(line)
            continue

        # Process normal line
        new_line = process_line(line, line_num, stats, warnings)

        if new_line != line:
            stats["lines_changed"] += 1

        result_lines.append(new_line)

    return "\n".join(result_lines)


def collect_files(input_path: Path, pattern: str) -> list[Path]:
    """
    Collect files to process.

    If input_path is a file, return it as a single-element list.
    If input_path is a directory, recursively glob for the given pattern.
    """
    if input_path.is_file():
        return [input_path]

    if input_path.is_dir():
        files = sorted(input_path.rglob(pattern))
        return files

    return []


def make_stats() -> dict:
    """Create a fresh statistics dictionary."""
    return {
        "straight_double": 0,
        "english_double": 0,
        "english_single": 0,
        "lines_changed": 0,
        "warnings": 0,
    }


def print_diff(original: str, modified: str):
    """Display line-by-line differences between original and result."""
    orig_lines = original.split("\n")
    mod_lines = modified.split("\n")

    max_lines = max(len(orig_lines), len(mod_lines))
    changes_shown = 0

    for i in range(max_lines):
        orig = orig_lines[i] if i < len(orig_lines) else ""
        mod = mod_lines[i] if i < len(mod_lines) else ""

        if orig != mod:
            print(f"  Line {i + 1}:")
            print(f"    - {orig.rstrip()}")
            print(f"    + {mod.rstrip()}")
            changes_shown += 1

    if changes_shown == 0:
        print("  No changes.")


def print_stats(stats: dict):
    """Print the summary statistics for a single file or aggregated run."""
    total_replacements = (
        stats["straight_double"] + stats["english_double"] + stats["english_single"]
    )

    print(f"  Straight \" -> German:       {stats['straight_double']} pair(s)")
    print(f"  English typographic double: {stats['english_double']} correction(s)")
    print(f"  English typographic single: {stats['english_single']} correction(s)")
    print(f"  Lines changed:              {stats['lines_changed']}")
    print(f"  Warnings (asymmetric):      {stats['warnings']}")
    print(f"  Total replacements:         {total_replacements}")


def process_single_file(
    file_path: Path, dry_run: bool, global_stats: dict
) -> list[str]:
    """
    Process a single file: read, convert, optionally write.

    Returns a list of warning strings. Updates global_stats in-place.
    """
    content = file_path.read_text(encoding="utf-8")

    stats = make_stats()
    warnings: list[str] = []

    result = process_file(content, stats, warnings)

    # Accumulate into global stats
    for key in global_stats:
        global_stats[key] += stats[key]

    total = stats["straight_double"] + stats["english_double"] + stats["english_single"]

    if total == 0 and not warnings:
        return warnings

    if dry_run:
        print(f"\n--- {file_path} (dry-run) ---")
        print_diff(content, result)
    else:
        if result != content:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup_path)
            file_path.write_text(result, encoding="utf-8")
            print(f"  Written: {file_path} (backup: {backup_path})")
        else:
            print(f"  Unchanged: {file_path}")

    return warnings


def main():
    args = parse_args()
    input_path: Path = args.input

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    files = collect_files(input_path, args.pattern)

    if not files:
        print(
            f"Error: No files matching '{args.pattern}' found in: {input_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    if input_path.is_dir():
        print(
            f"Processing {len(files)} file(s) in: {input_path} "
            f"(pattern: {args.pattern})"
        )

    global_stats = make_stats()
    all_warnings: list[str] = []

    for file_path in files:
        file_warnings = process_single_file(file_path, args.dry_run, global_stats)
        # Prefix warnings with file path for directory mode
        for w in file_warnings:
            all_warnings.append(f"[{file_path}] {w}")

    # Print warnings to stderr
    if all_warnings:
        print("\n--- WARNINGS ---", file=sys.stderr)
        for w in all_warnings:
            print(f"  WARNING: {w}", file=sys.stderr)
        print(f"--- {len(all_warnings)} warning(s) ---\n", file=sys.stderr)

    # Summary
    print("\n--- Summary ---")
    if input_path.is_dir():
        print(f"  Files processed:            {len(files)}")
    print_stats(global_stats)

    if args.dry_run:
        print("\nNo files written (--dry-run).")


if __name__ == "__main__":
    main()
