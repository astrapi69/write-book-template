from __future__ import annotations
from pathlib import Path

class ProjectPaths:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.book_dir = self.root / "manuscript"
        self.output_dir = self.root / "output"
        self.backup_dir = self.root / "output_backup"
        self.script_dir = self.root / "scripts"
        self.assets_dir = self.root / "assets"
        self.config_dir = self.root / "config"
        self.metadata_file = self.config_dir / "metadata.yaml"
        self.pyproject = self.root / "pyproject.toml"
        self.toc_file = self.book_dir / "front-matter" / "toc.md"
        self.normalizer = self.script_dir / "normalize_toc_links.py"
        self.conv_abs = self.script_dir / "convert_to_absolute.py"
        self.conv_rel = self.script_dir / "convert_to_relative.py"
        self.img_script = self.script_dir / "convert_img_tags.py"
