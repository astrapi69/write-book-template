from __future__ import annotations
from pathlib import Path
import toml, yaml, tempfile

DEFAULT_METADATA = "title: 'CHANGE TO YOUR TITLE'\nauthor: 'YOUR NAME'\ndate: '2025'\nlang: 'en'\n"

def get_project_name(pyproject: Path) -> str:
    try:
        data = toml.load(pyproject)
        return (
            data.get("tool", {}).get("poetry", {}).get("name") or
            data.get("project", {}).get("name") or
            "book"
        )
    except Exception as e:
        print(f"⚠️ Could not read project name from {pyproject}: {e}")
        return "book"

def get_metadata_lang(metadata_file: Path) -> str | None:
    if not metadata_file.exists():
        return None
    with metadata_file.open("r", encoding="utf-8") as f:
        try:
            meta = yaml.safe_load(f) or {}
            return meta.get("language") or meta.get("lang")
        except yaml.YAMLError as e:
            print(f"⚠️ Failed to parse {metadata_file}: {e}")
            return None

def get_or_create_metadata_file(preferred: Path):
    if preferred.exists():
        return preferred, False
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    tmp.write(DEFAULT_METADATA.encode("utf-8"))
    tmp.flush(); tmp.close()
    return Path(tmp.name), True
