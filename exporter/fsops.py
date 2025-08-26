from __future__ import annotations
from pathlib import Path
import shutil

def prepare_output_folder(output_dir: Path, backup_dir: Path, verbose: bool=False):
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
        if verbose: print("📦 Deleted old backup directory.")
    if output_dir.exists() and any(output_dir.iterdir()):
        shutil.move(str(output_dir), str(backup_dir))
        if verbose: print("📁 Moved current output to backup directory.")
    output_dir.mkdir(parents=True, exist_ok=True)
    if verbose: print("📂 Created clean output directory.")
