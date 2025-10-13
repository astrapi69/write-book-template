#!/usr/bin/env python3
# scripts/make_tag_message.py
"""
Make an AI-ready tag message prompt from git history and (optionally) create the tag.

Usage examples:
  # 1) Generate history + prompt for develop-de and tag v1.6.1-de
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de

  # 2) Only include commits since a ref (e.g., last German tag)
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de --range v1.6.0-de..develop-de

  # 3) Auto-detect last tag and use as range
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de --since-tag auto

  # 4) Create the tag from a prepared message file and push
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de --create-tag --push \
    --message-file dist/releases/TAGMSG_v1.6.1-de.txt

  # 5) Interactive mode (asks for missing values and confirmations)
  python scripts/make_tag_message.py --interactive

  # 6) Dry run to check everything before execution
  python scripts/make_tag_message.py --branch develop-de --tag v1.6.1-de --dry-run
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional fancy prompts
try:
    import questionary  # type: ignore
except Exception:
    questionary = None  # graceful fallback to input()

# Improved default pretty format that enables reliable filtering
DEFAULT_PRETTY_FORMAT = (
    "--pretty=format:commit %H%nAuthor: %an <%ae>%nDate: %ad%nSubject: %s%n%n%b%n"
)

# Template configurations
TEMPLATES = {
    "de": {
        "title_template": "Version {version_label} — <short theme>",
        "sections": [
            "**Content & Style**",
            "**Imagery & Accessibility**",
            "**Structure & Typography**",
            "**Metadata & Build**",
        ],
        "audience": "Readers of the German edition (non‑technical, okay with brief technical notes)",
        "conclusion": "Conclude with one sentence on the release purpose (production‑ready, accessibility, cohesion).",
    },
    "en": {
        "title_template": "Version {version_label} — <brief summary>",
        "sections": [
            "**Features & Content**",
            "**User Experience**",
            "**Technical Improvements**",
            "**Infrastructure & Build**",
        ],
        "audience": "End users and technical stakeholders",
        "conclusion": "Conclude with one sentence on the release's main value proposition.",
    },
}


def get_template_prompt(
    template_name: str, branch: str, tag: str, version_label: str, git_log: str
) -> str:
    """Generate prompt using specified template."""
    template = TEMPLATES.get(template_name, TEMPLATES["de"])

    sections_text = "\n   - ".join(template["sections"])

    return f"""**Role:** You are a release notes editor.

**Input:** I'll give you raw `git log` output from branch **{branch}**.

**Task:** Create a concise, user‑facing **tag message** for a release tag named **{tag}**.

**Audience:** {template["audience"]}.

**Requirements:**
1. Title line: `{template["title_template"]}`
2. Four sections with bullets:
   - {sections_text}
3. Group related commits; avoid duplicates; no internal refs or ticket IDs.
4. Use crisp verbs: *Added, Refined, Fixed, Unified, Reordered*.
5. Keep it concise and concrete (no marketing fluff).
6. {template["conclusion"]}

**Now rewrite the following `git log` into that tag message format:**

```
{git_log}
```
"""


class GitOperations:
    """Isolated git operations with error handling."""

    @staticmethod
    def run(cmd: List[str], cwd: Optional[str] = None) -> str:
        """Run git command with proper error handling."""
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True,
            encoding="utf-8",
        )
        if res.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
        return res.stdout.strip()

    @classmethod
    def get_log(
        cls,
        branch: str,
        rev_range: Optional[str],
        pretty: str,
        include_patches: bool,
        extra_args: List[str],
        max_commits: Optional[int] = None,
        patches_mode: Optional[str] = None,
    ) -> str:
        """Get git log with optional commit limit and patch modes."""
        base_cmd = ["git", "log", pretty]
        if include_patches:
            if patches_mode == "brief":
                base_cmd.extend(["-p", "-U1"])
            elif patches_mode == "full":
                base_cmd.append("-p")
        if max_commits:
            base_cmd.extend([f"-n{max_commits}"])
        if rev_range:
            base_cmd.append(rev_range)
        else:
            base_cmd.append(branch)
        base_cmd.extend(extra_args)

        return cls.run(base_cmd)

    @classmethod
    def get_last_tag(cls, branch: str, pattern: Optional[str] = None) -> Optional[str]:
        """Get the most recent tag on the branch, optionally matching pattern."""
        try:
            cmd = ["git", "describe", "--tags", "--abbrev=0"]
            if pattern:
                cmd.extend(["--match", pattern])
            cmd.append(branch)
            return cls.run(cmd)
        except RuntimeError:
            return None

    @classmethod
    def tag_exists_local(cls, tag: str) -> bool:
        """Check if tag exists locally."""
        try:
            cls.run(["git", "rev-parse", f"refs/tags/{tag}"])
            return True
        except RuntimeError:
            return False

    @classmethod
    def tag_exists_remote(cls, tag: str, remote: str = "origin") -> bool:
        """Check if tag exists on remote."""
        try:
            # Check for both refs/tags/<tag> and <tag> patterns for robustness
            out = cls.run(
                ["git", "ls-remote", "--tags", remote, f"refs/tags/{tag}", tag]
            )
            return bool(out.strip())
        except RuntimeError:
            return False

    @classmethod
    def count_commits(cls, rev_range: str) -> int:
        """Count commits in range."""
        try:
            result = cls.run(["git", "rev-list", "--count", rev_range])
            return int(result)
        except (RuntimeError, ValueError):
            return 0


class LogProcessor:
    """Process and filter git logs with improved reliability."""

    @staticmethod
    def filter_log(raw: str, exclude_subject_patterns: List[str]) -> str:
        """Filter log entries by subject patterns with improved detection."""
        if not exclude_subject_patterns:
            return raw

        out_lines = []
        lower_patterns = [p.lower() for p in exclude_subject_patterns]
        keep_block = True
        buffer_block: List[str] = []

        def is_commit_boundary(line: str) -> bool:
            return line.startswith("commit ")

        def extract_subject_from_block(block: List[str]) -> Optional[str]:
            """Extract subject from commit block, handling various formats."""
            # Look for explicit Subject: line first
            for line in block:
                if line.strip().lower().startswith("subject:"):
                    return line.split(":", 1)[1].strip().lower()

            # Fallback: find first non-empty line after headers (commit/Author/Date) and first blank line
            found_commit = False
            found_author = False
            found_date = False
            found_blank = False

            for line in block:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()

                if line_lower.startswith("commit"):
                    found_commit = True
                    continue
                elif found_commit and line_lower.startswith("author:"):
                    found_author = True
                    continue
                elif found_author and line_lower.startswith("date:"):
                    found_date = True
                    continue
                elif found_date and not line_stripped:
                    found_blank = True
                    continue
                elif found_blank and line_stripped:
                    return line_stripped.lower()

            return None

        def flush_if_kept():
            nonlocal buffer_block, out_lines, keep_block
            if keep_block and buffer_block:
                out_lines.extend(buffer_block)
            buffer_block = []
            keep_block = True

        for line in raw.splitlines():
            if is_commit_boundary(line) and buffer_block:
                # Process previous block
                subject = extract_subject_from_block(buffer_block)
                if subject and any(pat in subject for pat in lower_patterns):
                    keep_block = False
                flush_if_kept()

            buffer_block.append(line)

        # Process final block
        if buffer_block:
            subject = extract_subject_from_block(buffer_block)
            if subject and any(pat in subject for pat in lower_patterns):
                keep_block = False
            flush_if_kept()

        return "\n".join(out_lines)

    @staticmethod
    def categorize_commits(log_text: str) -> Dict[str, List[Dict[str, str]]]:
        """Categorize commits for JSON output."""
        commits = []
        current_commit: Dict[str, Any] = {}

        for line in log_text.split("\n"):
            line = line.strip()
            if line.startswith("commit "):
                if current_commit:
                    commits.append(current_commit)
                current_commit = {
                    "hash": line.split()[1],
                    "subject": "",
                    "author": "",
                    "date": "",
                }
            elif line.startswith("Author: "):
                current_commit["author"] = line[8:]
            elif line.startswith("Date: "):
                current_commit["date"] = line[6:]
            elif line.startswith("Subject: "):
                current_commit["subject"] = line[9:]
            elif (
                not current_commit.get("subject")
                and line
                and not line.startswith(("Author:", "Date:"))
            ):
                # Fallback for subject extraction
                current_commit["subject"] = line

        if current_commit:
            commits.append(current_commit)

        # Simple categorization based on subject keywords
        categories: Dict[str, Any] = {
            "content_style": [],
            "imagery_accessibility": [],
            "structure_typography": [],
            "metadata_build": [],
            "other": [],
        }

        for commit in commits:
            subject_lower = commit["subject"].lower()
            if any(
                word in subject_lower for word in ["content", "text", "style", "css"]
            ):
                categories["content_style"].append(commit)
            elif any(
                word in subject_lower
                for word in ["image", "img", "accessibility", "a11y", "alt"]
            ):
                categories["imagery_accessibility"].append(commit)
            elif any(
                word in subject_lower
                for word in ["structure", "layout", "typography", "font"]
            ):
                categories["structure_typography"].append(commit)
            elif any(
                word in subject_lower
                for word in ["build", "ci", "deploy", "config", "meta"]
            ):
                categories["metadata_build"].append(commit)
            else:
                categories["other"].append(commit)

        return categories


def write_file(path: Path, content: str) -> None:
    """Write file with directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_tag(tag: str) -> None:
    """Validate tag format."""
    if not tag:
        raise SystemExit("Tag is required (e.g., v1.6.1-de).")
    if " " in tag or "\n" in tag or "\t" in tag:
        raise SystemExit("Tag must not contain spaces, newlines, or tabs.")


def preflight_checks(args: argparse.Namespace) -> List[str]:
    """Perform preflight checks and return list of warnings/errors."""
    issues = []

    # Check if tag already exists
    if GitOperations.tag_exists_local(args.tag):
        issues.append(f"⚠️  Tag '{args.tag}' already exists locally")

    if GitOperations.tag_exists_remote(args.tag):
        issues.append(f"⚠️  Tag '{args.tag}' already exists on remote")
        # Add remediation guidance
        issues.append(
            f"    💡 To fix: git tag -d {args.tag} && git push --delete origin {args.tag}"
        )

    # Check message file if creating tag
    if args.create_tag:
        message_file = Path(
            args.message_file or f"{args.output_dir}/TAGMSG_{args.tag}.txt"
        )
        if not message_file.exists():
            issues.append(f"❌ Message file not found: {message_file}")
        elif message_file.stat().st_size == 0:
            issues.append(f"❌ Message file is empty: {message_file}")

    # Check commit count if range specified
    if args.rev_range:
        commit_count = GitOperations.count_commits(args.rev_range)
        if commit_count > 1000:
            issues.append(
                f"⚠️  Large commit range: {commit_count} commits (consider --max-commits)"
            )
        elif commit_count == 0:
            issues.append(f"❌ No commits found in range: {args.rev_range}")

    return issues


def ask_text(prompt: str, default: Optional[str] = None, validate=None) -> str:
    """Question helper with questionary fallback."""
    if questionary:
        ans = questionary.text(prompt, default=default or "").ask()
        if ans is None:
            raise SystemExit("Aborted.")
    else:
        ans = input(f"{prompt} " + (f"[{default}] " if default else "")).strip() or (
            default or ""
        )
    if validate:
        validate(ans)
    return ans


def ask_confirm(prompt: str, default: bool = False) -> bool:
    """Confirmation helper."""
    if questionary:
        return bool(questionary.confirm(prompt, default=default).ask())
    else:
        raw = input(f"{prompt} [{'Y/n' if default else 'y/N'}] ").strip().lower()
        if not raw:
            return default
        return raw in ("y", "yes", "j", "ja", "true", "1")


def ask_choice(prompt: str, choices: List[str], default: Optional[str] = None) -> str:
    """Choice helper."""
    if questionary:
        return questionary.select(prompt, choices=choices, default=default).ask()
    else:
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{marker}")

        while True:
            ans = input("Select: ").strip()
            if not ans and default:
                return default
            try:
                idx = int(ans) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                if ans in choices:
                    return ans
            print("Invalid selection, please try again.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Generate AI-ready tag message prompt from git history and (optionally) create the tag."
    )
    ap.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for missing values and confirmations.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing.",
    )
    ap.add_argument(
        "--branch",
        default=None,
        help="Branch to read history from (default: develop-de)",
    )
    ap.add_argument("--tag", help="Tag name to prepare (e.g., v1.6.1-de)")
    ap.add_argument(
        "--range", dest="rev_range", help="Git rev range (e.g., v1.6.0-de..develop-de)."
    )
    ap.add_argument(
        "--since-tag", help="Use 'auto' to auto-detect last tag, or specify tag name."
    )
    ap.add_argument(
        "--pretty",
        default=DEFAULT_PRETTY_FORMAT,
        help="git log pretty format (default: reliable format for filtering)",
    )
    ap.add_argument(
        "--patches",
        choices=["none", "brief", "full"],
        default="none",
        help="Include diffs: none, brief (-U1), or full (-p).",
    )
    ap.add_argument(
        "--max-commits",
        type=int,
        help="Maximum number of commits to include (default: unlimited).",
    )
    ap.add_argument(
        "--since", help='Only include commits since date (e.g., "2025-08-01").'
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=["chore", "merge", "wip"],
        help="Case-insensitive subject substrings to exclude.",
    )
    ap.add_argument(
        "--output-dir",
        default="dist/releases",
        help="Where to write files (default: dist/releases)",
    )
    ap.add_argument(
        "--template",
        choices=list(TEMPLATES.keys()),
        default="de",
        help="Template to use for prompt generation.",
    )
    ap.add_argument(
        "--template-file", help="Custom template file path (overrides --template)."
    )
    ap.add_argument(
        "--emit-json",
        action="store_true",
        help="Also emit JSON categorized commit summary.",
    )
    ap.add_argument(
        "--message-file",
        help="If set with --create-tag, read the tag message from this file.",
    )
    ap.add_argument(
        "--create-tag",
        action="store_true",
        help="Create the annotated tag from the message file.",
    )
    ap.add_argument(
        "--push", action="store_true", help="Push the created tag to origin."
    )
    ap.add_argument(
        "--auto-stub",
        action="store_true",
        help="Create empty TAGMSG_<tag>.txt stub file for convenience.",
    )
    ap.add_argument(
        "--force-stub",
        action="store_true",
        help="Overwrite existing TAGMSG_<tag>.txt stub file.",
    )
    return ap


def resolve_since_tag(args: argparse.Namespace) -> None:
    """Resolve --since-tag auto to actual tag name."""
    if args.since_tag == "auto":
        # Try to detect pattern from tag name
        pattern = None
        if args.tag:
            # Extract pattern like "*-de" from "v1.6.1-de"
            match = re.search(r"(.+?)(\d+\.\d+\.\d+)(.+)", args.tag)
            if match:
                prefix, _, suffix = match.groups()
                pattern = f"{prefix}*{suffix}"

        last_tag = None
        branch = args.branch or "develop-de"

        # Try git tag --list with pattern first (more predictable)
        if pattern:
            try:
                cmd = ["git", "tag", "--list", pattern, "--sort=-creatordate"]
                result = GitOperations.run(cmd)
                if result:
                    last_tag = result.split("\n")[0]
            except RuntimeError:
                pass

        # Fallback to git describe
        if not last_tag:
            last_tag = GitOperations.get_last_tag(branch, pattern)

        if last_tag:
            args.rev_range = f"{last_tag}..{branch}"
            print(f"🔍 Auto-detected range: {args.rev_range}")
        else:
            print("⚠️  No previous tag found, using full branch history")


def fill_from_interactive(args: argparse.Namespace) -> argparse.Namespace:
    """Fill arguments interactively."""
    # Defaults
    default_branch = args.branch or "develop-de"

    # Ask core parameters
    args.branch = ask_text("Branch:", default=default_branch)
    args.tag = ask_text(
        "Tag (e.g., v1.6.1-de):", default=args.tag or "", validate=validate_tag
    )

    # Template selection
    if len(TEMPLATES) > 1:
        args.template = ask_choice(
            "Template:", list(TEMPLATES.keys()), default=args.template
        )

    # Range selection
    range_options = [
        "Full branch history",
        "Since last tag (auto)",
        "Custom range",
        "Since date",
    ]
    range_choice = ask_choice("Commit range:", range_options, default=range_options[0])

    if range_choice == "Since last tag (auto)":
        args.since_tag = "auto"
    elif range_choice == "Custom range":
        args.rev_range = ask_text("Rev range (e.g., v1.6.0-de..develop-de):")
    elif range_choice == "Since date":
        args.since = ask_text("Since date (YYYY-MM-DD):")

    # Advanced options
    if ask_confirm("Configure advanced options?", default=False):
        if ask_confirm("Include patches for precision?", default=False):
            args.patches = ask_choice(
                "Patch detail:", ["brief", "full"], default="brief"
            )

        if ask_confirm("Limit number of commits?", default=False):
            args.max_commits = int(ask_text("Max commits:", default="100"))

        args.emit_json = ask_confirm("Emit JSON summary?", default=args.emit_json)

    # Tag creation flow
    if ask_confirm("Create annotated tag?", default=args.create_tag):
        args.create_tag = True
        if not args.message_file:
            default_msg = f"{args.output_dir}/TAGMSG_{args.tag}.txt"
            args.message_file = ask_text("Tag message file path:", default=default_msg)
        if ask_confirm("Push tag to origin after creation?", default=args.push):
            args.push = True

    args.auto_stub = ask_confirm("Create empty message stub file?", default=True)

    return args


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Interactive fill-in if requested or if crucial values are missing
    need_prompt = args.interactive or (
        sys.stdin.isatty() and (not args.tag or not args.branch)
    )
    if need_prompt:
        args = fill_from_interactive(args)
    else:
        # Non-interactive defaults
        args.branch = args.branch or "develop-de"
        if not args.tag:
            parser.error(
                "--tag is required in non-interactive mode. Use --interactive to be prompted."
            )

    validate_tag(args.tag)

    # Resolve auto since-tag
    if args.since_tag:
        resolve_since_tag(args)

    # Preflight checks
    issues = preflight_checks(args)
    if issues:
        print("\n🔍 Preflight check results:")
        for issue in issues:
            print(f"  {issue}")

        if any("❌" in issue for issue in issues):
            print("\n❌ Critical issues found. Please fix before proceeding.")
            if not args.dry_run:
                sys.exit(1)

        if not args.dry_run and args.interactive:
            if not ask_confirm("\nProceed despite warnings?", default=False):
                raise SystemExit("Aborted by user.")

    # Setup paths
    out_dir = Path(args.output_dir)
    _ = datetime.now().strftime("%Y%m%d-%H%M%S")

    def _sanitize_filename(name: str) -> str:
        """Sanitize filename component to avoid filesystem issues."""
        return re.sub(r"[^A-Za-z0-9._-]+", "_", name)

    history_name = (
        f"{args.branch}-history.txt"
        if not args.rev_range
        else f"{args.branch}-history_{_sanitize_filename(args.rev_range).replace('..', '__')}.txt"
    )
    history_path = out_dir / history_name
    prompt_path = out_dir / f"PROMPT_{args.tag}.md"
    tagmsg_path = out_dir / f"TAGMSG_{args.tag}.txt"
    json_path = out_dir / f"COMMITS_{args.tag}.json"

    if args.dry_run:
        print("\n🏃 DRY RUN - showing what would be executed:")
        print(f"  📝 History file : {history_path}")
        print(f"  🤖 Prompt file  : {prompt_path}")
        if args.emit_json:
            print(f"  📊 JSON file    : {json_path}")
        if args.auto_stub:
            print(f"  📄 Stub file    : {tagmsg_path}")
        if args.create_tag:
            print(
                f"  🏷️  Create tag   : {args.tag} from {args.message_file or tagmsg_path}"
            )
            if args.push:
                print(f"  📤 Push tag     : {args.tag} to origin")
        return

    # Prepare git log arguments
    extra_args: List[str] = []
    if args.since:
        extra_args.extend(["--since", args.since])

    include_patches = args.patches != "none"

    # Echo resolved parameters for debugging
    print(f"🔍 Fetching git log from {args.branch}...")
    print(f"    Range: {args.rev_range or 'full branch'}")
    print(f"    Pretty: {args.pretty}")
    print(f"    Patches: {args.patches}")
    if args.max_commits:
        print(f"    Max commits: {args.max_commits}")
    if args.since:
        print(f"    Since: {args.since}")

    # Get git log
    raw_log = GitOperations.get_log(
        branch=args.branch,
        rev_range=args.rev_range,
        pretty=args.pretty,
        include_patches=include_patches,
        extra_args=extra_args,
        max_commits=args.max_commits,
        patches_mode=args.patches if include_patches else None,
    )

    # Filter log
    print(f"🧹 Filtering commits (excluding: {', '.join(args.exclude)})...")
    filtered = LogProcessor.filter_log(raw_log, args.exclude)
    write_file(history_path, filtered)

    # Generate prompt
    version_label = (
        args.tag.replace("v", "", 1) if args.tag.startswith("v") else args.tag
    )

    if args.template_file:
        # Load custom template
        template_content = Path(args.template_file).read_text(encoding="utf-8")
        prompt = template_content.format(
            branch=args.branch,
            tag=args.tag,
            version_label=version_label,
            git_log=filtered.strip(),
        )
    else:
        prompt = get_template_prompt(
            args.template, args.branch, args.tag, version_label, filtered.strip()
        )

    # Add max-commits note if truncated
    if args.max_commits:
        prompt = (
            f"_Note: Output limited to {args.max_commits} most recent commits for brevity._\n\n"
            + prompt
        )

    write_file(prompt_path, prompt)

    # Generate JSON summary if requested
    if args.emit_json:
        print("📊 Generating JSON commit summary...")
        categories = LogProcessor.categorize_commits(filtered)
        json_summary = {
            "tag": args.tag,
            "branch": args.branch,
            "timestamp": datetime.now().isoformat(),
            "total_commits": sum(len(commits) for commits in categories.values()),
            "categories": categories,
        }
        write_file(json_path, json.dumps(json_summary, indent=2))

    # Create stub file if requested
    if args.auto_stub and (not tagmsg_path.exists() or args.force_stub):
        write_file(
            tagmsg_path,
            f"# Tag message for {args.tag}\n# Paste AI-generated content here\n",
        )

    # Output summary
    print("\n✅ Generated files:")
    print(f"  📝 History: {history_path}")
    print(f"  🤖 AI Prompt: {prompt_path}")
    if args.emit_json:
        print(f"  📊 JSON Summary: {json_path}")
    if args.auto_stub and tagmsg_path.exists():
        print(f"  📄 Message Stub: {tagmsg_path}")

    print("\n💡 Next steps:")
    print(f"  1. Copy the prompt from {prompt_path.name}")
    print("  2. Paste into your AI assistant")
    print(f"  3. Save the AI output to {tagmsg_path.name}")
    print("  4. Run with --create-tag --push to finalize")

    # Tag creation flow
    if args.create_tag:
        message_file = Path(args.message_file or tagmsg_path)
        if not message_file.exists():
            raise SystemExit(
                f"--create-tag specified, but message file not found:\n  {message_file}\n"
                f"➡️ Tip: Save the AI output to this path first"
            )

        if message_file.stat().st_size < 10:  # Basic non-empty check
            raise SystemExit(
                f"Message file appears to be empty or too small: {message_file}"
            )

        # Final confirmation
        if args.interactive:
            if not ask_confirm(
                f"Create tag {args.tag} at {args.branch} using {message_file}?",
                default=True,
            ):
                raise SystemExit("Aborted before tag creation.")

        print(f"🏷️  Creating tag {args.tag}...")
        GitOperations.run(
            ["git", "tag", "-a", args.tag, "-F", str(message_file), args.branch]
        )
        print(f"✅ Created tag {args.tag} at {args.branch}")

        if args.push:
            if args.interactive and not ask_confirm(
                f"Push tag {args.tag} to origin?", default=True
            ):
                print("Skipped push.")
            else:
                print(f"📤 Pushing tag {args.tag}...")
                GitOperations.run(["git", "push", "origin", args.tag])
                print(f"✅ Pushed tag {args.tag} to origin")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        # Ensure dry-run exits with 0 for CI exploratory steps
        if "--dry-run" in sys.argv:
            sys.exit(0)
        else:
            sys.exit(e.code)
