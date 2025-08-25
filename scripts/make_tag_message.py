#!/usr/bin/env python3
# scripts/make_tag_message.py
"""
Make an AI-ready tag message prompt from git history and (optionally) create the tag.

Usage examples:
  # 1) Generate history + prompt for develop-de and tag v1.6.1-de
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de

  # 2) Only include commits since a ref (e.g., last German tag)
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de --range v1.6.0-de..develop-de

  # 3) Create the tag from a prepared message file and push
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de --create-tag --push \
    --message-file dist/releases/TAGMSG_v1.6.1-de.txt

  # 4) Interactive mode (asks for missing values and confirmations)
  python scripts/make_tag_message.py --interactive
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Optional fancy prompts
try:
    import questionary  # type: ignore
except Exception:
    questionary = None  # graceful fallback to input()

PROMPT_TEMPLATE = """**Role:** You are a release notes editor.

**Input:** I’ll give you raw `git log` output from branch **{branch}**.

**Task:** Create a concise, user‑facing **tag message** for a release tag named **{tag}** (German edition).

**Audience:** Readers of the German edition (non‑technical, okay with brief technical notes).

**Requirements:**
1. Title line: `Version {version_label} – <short theme>`
2. Four sections with bullets:
   - **Content & Style**
   - **Imagery & Accessibility**
   - **Structure & Typography**
   - **Metadata & Build**
3. Group related commits; avoid duplicates; no internal refs or ticket IDs.
4. Use crisp verbs: *Added, Refined, Fixed, Unified, Reordered*.
5. Keep it concise and concrete (no marketing fluff).
6. Conclude with one sentence on the release purpose (production‑ready, accessibility, cohesion).

**Now rewrite the following `git log` into that tag message format:**

```
{git_log}
```
"""

def run(cmd: List[str], cwd: Optional[str] = None) -> str:
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
    return res.stdout

def get_git_log(branch: str, rev_range: Optional[str], pretty: str, include_patches: bool, extra_args: List[str]) -> str:
    base_cmd = ["git", "log", pretty]
    if include_patches:
        base_cmd.append("-p")
    if rev_range:
        base_cmd.append(rev_range)
    else:
        base_cmd.append(branch)
    base_cmd.extend(extra_args)
    return run(base_cmd)

def filter_log(raw: str, exclude_subject_patterns: List[str]) -> str:
    if not exclude_subject_patterns:
        return raw
    out_lines = []
    lower_patterns = [p.lower() for p in exclude_subject_patterns]
    keep_block = True
    buffer_block: List[str] = []

    def commit_boundary(line: str) -> bool:
        return line.startswith("commit ")

    def flush_if_kept():
        nonlocal buffer_block, out_lines, keep_block
        if keep_block and buffer_block:
            out_lines.extend(buffer_block)
        buffer_block = []
        keep_block = True

    for line in raw.splitlines():
        if commit_boundary(line):
            flush_if_kept()
        buffer_block.append(line)

        if line.strip().lower().startswith("subject:"):
            subj = line.split(":", 1)[1].strip().lower()
            if any(pat in subj for pat in lower_patterns):
                keep_block = False

    flush_if_kept()
    return "\n".join(out_lines)

def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def validate_tag(tag: str) -> None:
    if not tag:
        raise SystemExit("Tag is required (e.g., v1.6.1-de).")
    # Basic safety (you can relax this if needed)
    if " " in tag or "\n" in tag:
        raise SystemExit("Tag must not contain spaces or newlines.")

def ask_text(prompt: str, default: Optional[str] = None, validate=None) -> str:
    """Question helper with questionary fallback."""
    if questionary:
        ans = questionary.text(prompt, default=default or "").ask()
        if ans is None:
            raise SystemExit("Aborted.")
    else:
        ans = input(f"{prompt} " + (f"[{default}] " if default else "")).strip() or (default or "")
    if validate:
        validate(ans)
    return ans

def ask_confirm(prompt: str, default: bool = False) -> bool:
    if questionary:
        return bool(questionary.confirm(prompt, default=default).ask())
    else:
        raw = input(f"{prompt} [{'Y/n' if default else 'y/N'}] ").strip().lower()
        if not raw:
            return default
        return raw in ("y", "yes", "j", "ja", "true", "1")

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Generate AI-ready tag message prompt from git history and (optionally) create the tag."
    )
    ap.add_argument("--interactive", action="store_true", help="Prompt for missing values and confirmations.")
    ap.add_argument("--branch", default=None, help="Branch to read history from (default: develop-de)")
    ap.add_argument("--tag", help="Tag name to prepare (e.g., v1.6.1-de)")
    ap.add_argument("--range", dest="rev_range", help="Git rev range (e.g., v1.6.0-de..develop-de).")
    ap.add_argument("--pretty", default="--pretty=full", help="git log pretty format (default: --pretty=full)")
    ap.add_argument("--patches", action="store_true", help="Include diffs (-p). Heavier but precise.")
    ap.add_argument("--since", help='Only include commits since date (e.g., "2025-08-01").')
    ap.add_argument("--exclude", nargs="*", default=["chore", "merge", "wip"], help="Case-insensitive subject substrings to exclude.")
    ap.add_argument("--output-dir", default="dist/releases", help="Where to write files (default: dist/releases)")
    ap.add_argument("--message-file", help="If set with --create-tag, read the tag message from this file.")
    ap.add_argument("--create-tag", action="store_true", help="Create the annotated tag from the message file.")
    ap.add_argument("--push", action="store_true", help="Push the created tag to origin.")
    return ap

def fill_from_interactive(args: argparse.Namespace) -> argparse.Namespace:
    # Defaults
    default_branch = args.branch or "develop-de"
    default_range = args.rev_range or ""
    default_since = args.since or ""

    # Ask core parameters
    args.branch = ask_text("Branch:", default=default_branch or "develop-de")
    args.tag = ask_text("Tag (e.g., v1.6.1-de):", default=args.tag or "", validate=validate_tag)
    args.rev_range = ask_text("Rev range (empty = full branch):", default=default_range) or None

    # Optional filters
    if ask_confirm("Filter by --since date (YYYY-MM-DD)?", default=bool(default_since)):
        args.since = ask_text("Since date:", default=default_since or "")

    # Include patches?
    if ask_confirm("Include patches (-p) for precision (larger output)?", default=args.patches):
        args.patches = True

    # Tag creation/push flow
    if ask_confirm("Create annotated tag now?", default=args.create_tag):
        args.create_tag = True
        if not args.message_file:
            # Suggest default tag message path
            default_msg = str(Path(args.output_dir) / f"TAGMSG_{args.tag}.txt")
            args.message_file = ask_text("Tag message file path:", default=default_msg)
        if ask_confirm("Push tag to origin after creation?", default=args.push):
            args.push = True

    return args

def main():
    parser = build_parser()
    args = parser.parse_args()

    # Interactive fill-in if requested or if crucial values are missing and we have a TTY.
    need_prompt = args.interactive or (sys.stdin.isatty() and (not args.tag or not args.branch))
    if need_prompt:
        args = fill_from_interactive(args)
    else:
        # Non-interactive defaults/backfill
        args.branch = args.branch or "develop-de"
        if not args.tag:
            parser.error("--tag is required in non-interactive mode. Use --interactive to be prompted.")

    validate_tag(args.tag)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.output_dir)
    history_name = (
        f"{args.branch}-history.txt"
        if not args.rev_range
        else f"{args.branch}-history_{args.rev_range.replace('..','__')}.txt"
    )
    history_path = out_dir / history_name
    prompt_path = out_dir / f"PROMPT_{args.tag}.md"
    tagmsg_path = out_dir / f"TAGMSG_{args.tag}.txt"

    extra: List[str] = []
    if args.since:
        extra.extend(["--since", args.since])

    # Small interactive safety preview
    if args.interactive:
        print("\nPlanned output:")
        print(f"  • History file : {history_path}")
        print(f"  • Prompt file  : {prompt_path}")
        if args.create_tag:
            print(f"  • Tag message  : {args.message_file or tagmsg_path}")
        if not ask_confirm("Proceed?", default=True):
            raise SystemExit("Aborted by user.")

    raw_log = get_git_log(
        branch=args.branch,
        rev_range=args.rev_range,
        pretty=args.pretty,
        include_patches=args.patches,
        extra_args=extra,
    )

    filtered = filter_log(raw_log, args.exclude)
    write_file(history_path, filtered)

    version_label = args.tag.replace("v", "", 1) if args.tag.startswith("v") else args.tag
    prompt = PROMPT_TEMPLATE.format(
        branch=args.branch,
        tag=args.tag,
        version_label=version_label,
        git_log=filtered.strip()
    )
    write_file(prompt_path, prompt)

    print(f"✔ Wrote history to: {history_path}")
    print(f"✔ Wrote AI prompt to: {prompt_path}")
    print(f"   (Paste {history_path.name} into the prompt where needed—already embedded above.)")

    if args.create_tag:
        message_file = args.message_file or str(tagmsg_path)
        if not Path(message_file).exists():
            raise SystemExit(
                f"--create-tag specified, but message file not found:\n  {message_file}\n"
                f"➡ Tip: Save the AI output to this path or pass --message-file PATH"
            )

        # Final confirmation before mutating repo (interactive only)
        if args.interactive and not ask_confirm(f"Create tag {args.tag} at {args.branch} using {message_file}?", default=True):
            raise SystemExit("Aborted before tag creation.")

        run(["git", "tag", "-a", args.tag, "-F", message_file, args.branch])
        print(f"✔ Created tag {args.tag} at {args.branch}")

        if args.push:
            if args.interactive and not ask_confirm(f"Push tag {args.tag} to origin?", default=True):
                print("Skipped push.")
            else:
                run(["git", "push", "origin", args.tag])
                print(f"✔ Pushed tag {args.tag} to origin")

if __name__ == "__main__":
    main()
