# scripts/reorder_and_rename_chapters.py
"""
Generic chapter reordering & renaming script with header/anchor normalization.

Features:
- Two-phase rename to avoid collisions (.tmpmove -> final)
- Update H1 to language-appropriate pattern and ensure "{#-chapter-N}" anchor
- Mapping can be passed inline (--map "src:tgt" ...) or loaded from file (--map-file)
- Supports JSON or CSV (2 columns: src,tgt). YAML if PyYAML is installed.
- Languages: DE/EN/ES (select via --lang) or auto-detect by H1 prefix
- Dry run mode

Usage examples:
  poetry run reorder-chapters --dry-run \
      --base-dir manuscript/chapters \
      --map-file mapping.json --lang es

  poetry run reorder-chapters --base-dir manuscript/chapters \
      --map 11-chapter.md:07-chapter.md \
      --map 14-chapter.md:08-chapter.md \
      --map 16-chapter.md:09-chapter.md

Exit codes:
  0 = success, 1 = configuration error
"""

from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path
import sys
from typing import Dict, Iterable, Optional, Tuple

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False

# -------- Language patterns --------

# Each entry: (H1 regex, H1 builder callable)
# H1 regex must capture: (prefix, number, rest, optional_anchor)
LANG_PATTERNS: Dict[str, Tuple[re.Pattern, callable]] = {
    "es": (
        re.compile(r'^(#\s+✦\s+Cap[ií]tulo\s+)(\d+)(:.*?)(\s*\{#-chapter-\d+\}\s*)?$', re.IGNORECASE),
        lambda num, rest: f"# ✦ Capítulo {num}{rest} {{#-chapter-{num}}}",
    ),
    "de": (
        re.compile(r'^(#\s+✦\s+Kapitel\s+)(\d+)(:.*?)(\s*\{#-chapter-\d+\}\s*)?$', re.IGNORECASE),
        lambda num, rest: f"# ✦ Kapitel {num}{rest} {{#-chapter-{num}}}",
    ),
    "en": (
        re.compile(r'^(#\s+✦\s+Chapter\s+)(\d+)(:.*?)(\s*\{#-chapter-\d+\}\s*)?$', re.IGNORECASE),
        lambda num, rest: f"# ✦ Chapter {num}{rest} {{#-chapter-{num}}}",
    ),
}

ANCHOR_ONLY_REGEX = re.compile(r'(\{#-chapter-)(\d+)(\})', re.IGNORECASE)

# -------- Mapping loaders --------

def load_mapping_file(path: Path) -> Dict[str, str]:
    """
    Load rename mapping from file.
    - JSON: object { "src": "tgt", ... } OR list of {"src": "...", "tgt": "..."}
    - CSV:  two columns: src,tgt (header optional)
    - YAML: same as JSON (requires PyYAML)
    """
    if not path.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")

    ext = path.suffix.lower()
    if ext in (".json",):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        if isinstance(data, list):
            out: Dict[str, str] = {}
            for row in data:
                src = row.get("src")
                tgt = row.get("tgt")
                if not src or not tgt:
                    raise ValueError("JSON list items must have 'src' and 'tgt'")
                out[str(src)] = str(tgt)
            return out
        raise ValueError("JSON mapping must be dict or list of {src,tgt}")

    if ext in (".csv",):
        out: Dict[str, str] = {}
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            try:
                first_row = next(reader)
            except StopIteration:
                return out  # empty file
            is_header = (
                    len(first_row) >= 2
                    and first_row[0].strip().lower() == "src"
                    and first_row[1].strip().lower() == "tgt"
            )
            if is_header:
                # Use DictReader on the rest, keep header names from first_row
                dict_reader = csv.DictReader(fh, fieldnames=[c.strip() for c in first_row])
                # Skip the header row already consumed
                for row in dict_reader:
                    src = row.get("src")
                    tgt = row.get("tgt")
                    if not src or not tgt:
                        raise ValueError("CSV with header must have columns 'src' and 'tgt'")
                    out[str(src)] = str(tgt)
            else:
                # Treat first row as data
                if len(first_row) < 2:
                    raise ValueError("CSV rows must have at least 2 columns: src,tgt")
                out[str(first_row[0])] = str(first_row[1])
                for row in reader:
                    if len(row) < 2:
                        raise ValueError("CSV rows must have at least 2 columns: src,tgt")
                    out[str(row[0])] = str(row[1])
        return out

    if ext in (".yml", ".yaml"):
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed. `poetry add pyyaml` or use JSON/CSV.")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        if isinstance(data, list):
            out: Dict[str, str] = {}
            for row in data:
                src = row.get("src")
                tgt = row.get("tgt")
                if not src or not tgt:
                    raise ValueError("YAML list items must have 'src' and 'tgt'")
                out[str(src)] = str(tgt)
            return out
        raise ValueError("YAML mapping must be dict or list of {src,tgt}")

    raise ValueError(f"Unsupported mapping file format: {ext}")


def parse_inline_map(items: Iterable[str]) -> Dict[str, str]:
    """
    Parse inline mapping entries like: "src:tgt"
    """
    out: Dict[str, str] = {}
    for it in items:
        if ":" not in it:
            raise ValueError(f"Invalid mapping '{it}'. Use 'src:tgt'.")
        src, tgt = it.split(":", 1)
        src = src.strip()
        tgt = tgt.strip()
        if not src or not tgt:
            raise ValueError(f"Invalid mapping '{it}'. Empty src/tgt.")
        out[src] = tgt
    return out

# -------- Header/anchor update --------

def autodetect_lang_by_header(text: str) -> Optional[str]:
    head = "\n".join(text.splitlines()[:5])
    if re.search(r'#\s+✦\s+Cap[ií]tulo\s+\d+', head, re.IGNORECASE):
        return "es"
    if re.search(r'#\s+✦\s+Kapitel\s+\d+', head, re.IGNORECASE):
        return "de"
    if re.search(r'#\s+✦\s+Chapter\s+\d+', head, re.IGNORECASE):
        return "en"
    return None

def update_header_and_anchor(file_path: Path, new_num: int, lang: Optional[str], dry_run: bool) -> None:
    text = file_path.read_text(encoding="utf-8")
    lang_eff = lang or autodetect_lang_by_header(text) or "es"  # default ES for this workflow
    if lang_eff not in LANG_PATTERNS:
        raise ValueError(f"Unsupported language '{lang_eff}'. Use one of: {', '.join(LANG_PATTERNS)}")

    h1_regex, h1_builder = LANG_PATTERNS[lang_eff]

    def _repl_h1(m: re.Match) -> str:
        _prefix, _old_num, rest, _anchor = m.groups()
        return h1_builder(new_num, rest)

    new_text, n1 = h1_regex.subn(_repl_h1, text, count=1)

    if n1 == 0:
        # Fallback: update first {#-chapter-X} occurrence
        new_text = ANCHOR_ONLY_REGEX.sub(rf"\1{new_num}\3", new_text, count=1)

    if dry_run:
        if new_text != text:
            print(f"[DRY] Would update header/anchor -> chapter {new_num} in {file_path.name} (lang={lang_eff})")
        return

    file_path.write_text(new_text, encoding="utf-8")
    print(f"[OK] {file_path.name}: header/anchor -> chapter {new_num} (lang={lang_eff})")

# -------- Main logic --------

def _resolve_mapping(map_file: Optional[Path], inline_map: Iterable[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if map_file:
        mapping.update(load_mapping_file(map_file))
    if inline_map:
        # inline overrides file for same src
        mapping.update(parse_inline_map(inline_map))
    if not mapping:
        raise ValueError("No mapping provided. Use --map-file and/or --map 'src:tgt'.")
    # sanity: unique targets
    targets = list(mapping.values())
    if len(targets) != len(set(targets)):
        raise ValueError("Target filename collision in mapping. Make targets unique.")
    return mapping

def _two_phase_rename(base_dir: Path, mapping: Dict[str, str], dry_run: bool) -> Dict[Path, Path]:
    """
    Return map: temp_path -> final_path
    """
    tmp_map: Dict[Path, Path] = {}

    # Phase 1: to temp
    for src, tgt in mapping.items():
        src_path = base_dir / src
        if not src_path.exists():
            print(f"[WARN] Source not found (skipping): {src_path}")
            continue
        tmp_path = src_path.with_suffix(src_path.suffix + ".tmpmove")
        if dry_run:
            print(f"[DRY] Would rename: {src_path.name} -> {tmp_path.name}")
        else:
            src_path.rename(tmp_path)
        tmp_map[tmp_path] = base_dir / tgt

    # Phase 2: to final
    for tmp_path, final_path in tmp_map.items():
        if dry_run:
            print(f"[DRY] Would finalize: {tmp_path.name} -> {final_path.name}")
        else:
            final_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.rename(final_path)

    return tmp_map

def main() -> int:
    ap = argparse.ArgumentParser(description="Reorder/rename chapter files and normalize H1 + {#-chapter-N}.")
    ap.add_argument("--base-dir", type=Path, default=Path("manuscript/chapters"),
                    help="Base directory containing chapter files (default: manuscript/chapters).")
    ap.add_argument("--map-file", type=Path, help="Mapping file (JSON, CSV, YAML).")
    ap.add_argument("--map", action="append", default=[],
                    help="Inline mapping 'src:tgt'. Can be used multiple times.")
    ap.add_argument("--lang", choices=list(LANG_PATTERNS.keys()),
                    help="Language for H1 normalization (de/en/es). If omitted, auto-detect per file.")
    ap.add_argument("--dry-run", action="store_true", help="Only print actions; do not modify files.")
    args = ap.parse_args()

    base_dir: Path = args.base_dir
    dry_run: bool = args.dry_run

    if not base_dir.exists():
        print(f"[ERROR] Base dir not found: {base_dir}", file=sys.stderr)
        return 1

    try:
        mapping = _resolve_mapping(args.map_file, args.map)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    # Two-phase rename
    tmp_map = _two_phase_rename(base_dir, mapping, dry_run=dry_run)

    # Update headers/anchors for all final files produced
    for _tmp_path, final_path in tmp_map.items():
        try:
            new_num = int(final_path.name.split("-")[0])
        except Exception:
            print(f"[WARN] Could not infer chapter number from filename: {final_path.name}")
            continue
        try:
            update_header_and_anchor(final_path, new_num, lang=args.lang, dry_run=dry_run)
        except Exception as e:
            print(f"[WARN] Header/anchor update failed for {final_path.name}: {e}")

    print("[DONE] Reorder/rename + header/anchor normalization complete." + (" (dry-run)" if dry_run else ""))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
