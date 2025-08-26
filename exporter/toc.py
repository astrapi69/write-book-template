from __future__ import annotations
import subprocess
from pathlib import Path

def normalize_toc(toc_file: Path, normalizer: Path, ext: str="md", mode: str="strip-to-anchors", log_file: Path|None=None):
    if not toc_file.exists():
        print(f"ℹ️  No TOC file at {toc_file}; skipping TOC normalization.")
        return
    cmd = ["python3", str(normalizer), "--toc", str(toc_file), "--mode", mode, "--ext", ext]
    with open(log_file, "a") if log_file else open("/dev/null","w") as log:
        subprocess.run(cmd, check=True, stdout=log, stderr=log)
    print(f"✅ TOC normalized using mode={mode}")
