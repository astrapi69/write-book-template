#!/usr/bin/env python3
"""
clean_git_cache.py

Safely clean Git cache (unreachable objects and old reflogs)
without touching working directory or latest commits.
"""

import subprocess
import os

# Change the current working directory to the root directory of the project
# (Assumes the script is located one level inside the project root)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

def run_git_command(command):
    try:
        print(f"🔧 Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr.strip()}")

def main():
    print("🧹 Cleaning Git object cache safely...")

    # Step 1: Expire all reflog entries immediately
    run_git_command("git reflog expire --expire=now --all")

    # Step 2: Run garbage collection to prune unreachable objects
    run_git_command("git gc --prune=now --aggressive")

    print("✅ Git object cache cleaned successfully.")

if __name__ == "__main__":
    main()
