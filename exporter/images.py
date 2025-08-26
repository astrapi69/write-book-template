from __future__ import annotations
import subprocess
from pathlib import Path

def run_script(script: Path, arg: str|None=None, log_file: Path|None=None):
    cmd = ["python3", str(script)]
    if arg: cmd.append(arg)
    with open(log_file, "a") if log_file else open("/dev/null","w") as log:
        subprocess.run(cmd, check=True, stdout=log, stderr=log)

def pre_image_steps(conv_abs: Path, img_script: Path, skip: bool, keep_rel: bool, log: Path|None):
    if skip:
        print("⏭️  Skipping Step 1 (skip-images)."); return
    if keep_rel:
        print("⏭️  Skipping Step 1 (keep relative paths)."); return
    run_script(conv_abs, None, log)
    run_script(img_script, "--to-absolute", log)

def post_image_steps(conv_rel: Path, img_script: Path, skip: bool, keep_rel: bool, log: Path|None):
    if skip:
        print("⏭️  Skipping Step 4 (skip-images)."); return
    if keep_rel:
        print("⏭️  Skipping Step 4 (keep relative paths)."); return
    run_script(conv_rel, None, log)
    run_script(img_script, "--to-relative", log)
