#!/usr/bin/env python3
# scripts/replace_md_bullet_points.py
import re
import sys
from pathlib import Path
from typing import Union


def convert_bullets_in_text(text: str, add_hard_break: bool = True) -> str:
    """
    Replace Markdown list markers (- or *) with •,
    preserve multi-line items and ignore fenced code blocks.
    By default, append two spaces (hard breaks) at the end of each list line.
    """
    lines = text.split("\n")
    new_lines = []

    in_list = False
    last_list_indent = 0
    in_code_block = False

    bullet_pattern = re.compile(r"^(\s*)([-*])\s+(.*)$")

    for line in lines:
        stripped = line.lstrip()

        # Enter/exit fenced code block (``` or ```lang)
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue

        if in_code_block:
            # Do not modify anything inside ```
            new_lines.append(line)
            continue

        indent = len(line) - len(stripped)

        # 1) New bullet line
        m = bullet_pattern.match(line)
        if m:
            leading_ws, bullet_char, content = m.groups()
            new_line = f"{leading_ws}• {content}"
            if add_hard_break:
                new_line += "  "
            new_lines.append(new_line)

            in_list = True
            last_list_indent = indent
            continue

        # 2) Continuation line of a multi-line bullet item
        if in_list and indent > last_list_indent and stripped != "":
            cont_line = line
            if add_hard_break:
                cont_line = cont_line + "  "
            new_lines.append(cont_line)
            continue

        # 3) Normal line → end list state
        new_lines.append(line)
        in_list = False

    return "\n".join(new_lines)


def process_file(path: Path, add_hard_break: bool = True) -> None:
    text = path.read_text(encoding="utf-8")
    fixed = convert_bullets_in_text(text, add_hard_break=add_hard_break)
    path.write_text(fixed, encoding="utf-8")
    print(f"[OK] {path}")


def process_path(target: Union[str, Path], add_hard_break: bool = True) -> None:
    """
    If target is a file -> process only this file.
    If target is a directory -> recursively process all .md files.
    """
    p = Path(target)

    if p.is_file():
        process_file(p, add_hard_break=add_hard_break)
    elif p.is_dir():
        for md_file in p.rglob("*.md"):
            process_file(md_file, add_hard_break=add_hard_break)
    else:
        print(f"[ERROR] Path not found: {p}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: replace_md_bullet_points.py <file-or-dir>")
        sys.exit(1)

    target = sys.argv[1]

    # Hard breaks are enabled by default
    process_path(target, add_hard_break=True)


if __name__ == "__main__":
    main()
