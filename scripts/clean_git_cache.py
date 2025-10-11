#!/usr/bin/env python3
# scripts/clean_git_cache.py
"""
clean_git_cache.py

Safely cleans Git object cache by expiring reflogs and pruning unreachable objects.
Designed to be testable (no side effects at import; no shell=True).
"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Optional


def run_git_command(
    args: Iterable[str], cwd: Optional[Path] = None
) -> subprocess.CompletedProcess:
    """
    Run a git command with robust defaults.

    Args:
        args: Iterable of command arguments, e.g., ["git", "gc", "--prune=now"].
        cwd: Directory in which to run the command (default: current working dir).

    Returns:
        The CompletedProcess object.

    Raises:
        subprocess.CalledProcessError if the command fails.
    """
    cmd = list(args)
    print(f"🔧 Running: {' '.join(cmd)}")
    cp = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
    )
    if cp.stdout:
        print(cp.stdout.strip())
    if cp.stderr:
        # git sometimes prints useful info on stderr even on success
        sys.stderr.write(cp.stderr.strip() + "\n")
    return cp


def clean_git_cache(
    cwd: Optional[Path] = None, aggressive: bool = True, prune: str = "now"
) -> None:
    """
    Expire reflogs and run git gc pruning unreachable objects.

    Args:
        cwd: Repository root. If None, uses current working directory.
        aggressive: Whether to pass --aggressive to git gc.
        prune: Prune spec (e.g., 'now', '1.week.ago').
    """
    print("🧹 Cleaning Git object cache safely...")

    # Step 1: Expire all reflog entries immediately (or at given prune spec)
    run_git_command(["git", "reflog", "expire", f"--expire={prune}", "--all"], cwd=cwd)

    # Step 2: Run garbage collection to prune unreachable objects
    gc_cmd = ["git", "gc", f"--prune={prune}"]
    if aggressive:
        gc_cmd.append("--aggressive")
    run_git_command(gc_cmd, cwd=cwd)

    print("✅ Git object cache cleaned successfully.")


def main() -> None:
    """
    CLI entry. Uses repository root = parent of this file’s directory,
    matching your original behavior but keeping it out of import-time side effects.
    """
    repo_root = Path(__file__).resolve().parent.parent
    try:
        clean_git_cache(cwd=repo_root, aggressive=True, prune="now")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr.strip() if e.stderr else e}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
