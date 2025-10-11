# tests/test_reorder_and_rename_chapters.py
import json
import csv
from pathlib import Path

import pytest

# Importiere direkt aus deinem Script
from scripts.reorder_and_rename_chapters import (
    load_mapping_file,
    parse_inline_map,
    update_header_and_anchor,
    _resolve_mapping,
    _two_phase_rename,
    autodetect_lang_by_header,
)

# ----------------------------
# Helpers
# ----------------------------


def write_chapter(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


ES_H1 = (
    "# ✦ Capítulo 11: Creatividad – La moneda renovable {#-chapter-11}\n\nContenido…\n"
)
DE_H1 = "# ✦ Kapitel 9: Mentale Klarheit – Der Kompass des Geistes {#-chapter-9}\n\nInhalt…\n"
EN_H1 = "# ✦ Chapter 7: Presence – The Lost Art of Being Rich Now {#-chapter-7}\n\nContent…\n"

# Header ohne Anchor (soll Fallback greifen)
ES_H1_NO_ANCHOR = "# ✦ Capítulo 16: Ideas – Semillas de riqueza mental\n\nContenido…\n"


# ----------------------------
# Mapping Loader Tests
# ----------------------------


def test_load_mapping_json_dict(tmp_path: Path):
    mf = tmp_path / "mapping.json"
    data = {"11-chapter.md": "07-chapter.md", "14-chapter.md": "08-chapter.md"}
    mf.write_text(json.dumps(data), encoding="utf-8")

    mapping = load_mapping_file(mf)
    assert mapping["11-chapter.md"] == "07-chapter.md"
    assert mapping["14-chapter.md"] == "08-chapter.md"


def test_load_mapping_json_list(tmp_path: Path):
    mf = tmp_path / "mapping.json"
    data = [{"src": "16-chapter.md", "tgt": "09-chapter.md"}]
    mf.write_text(json.dumps(data), encoding="utf-8")
    mapping = load_mapping_file(mf)
    assert mapping["16-chapter.md"] == "09-chapter.md"


def test_load_mapping_csv_with_header(tmp_path: Path):
    mf = tmp_path / "mapping.csv"
    with mf.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["src", "tgt"])
        w.writerow(["07-chapter.md", "10-chapter.md"])
    mapping = load_mapping_file(mf)
    assert mapping["07-chapter.md"] == "10-chapter.md"


def test_load_mapping_csv_no_header(tmp_path: Path):
    mf = tmp_path / "mapping.csv"
    with mf.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["08-chapter.md", "14-chapter.md"])
    mapping = load_mapping_file(mf)
    assert mapping["08-chapter.md"] == "14-chapter.md"


@pytest.mark.skipif(not pytest.importorskip("yaml"), reason="PyYAML not installed")
def test_load_mapping_yaml_list(tmp_path: Path):
    import yaml  # type: ignore

    mf = tmp_path / "mapping.yaml"
    data = [{"src": "21-chapter.md", "tgt": "15-chapter.md"}]
    mf.write_text(yaml.safe_dump(data), encoding="utf-8")
    mapping = load_mapping_file(mf)
    assert mapping["21-chapter.md"] == "15-chapter.md"


def test_parse_inline_map_ok():
    m = parse_inline_map(["11-chapter.md:07-chapter.md", "14-chapter.md:08-chapter.md"])
    assert m["11-chapter.md"] == "07-chapter.md"
    assert m["14-chapter.md"] == "08-chapter.md"


def test_parse_inline_map_invalid():
    with pytest.raises(ValueError):
        parse_inline_map(["broken_entry_without_colon"])


# ----------------------------
# Resolve Mapping Tests
# ----------------------------


def test_resolve_mapping_merges_and_detects_collisions(tmp_path: Path):
    # File mapping
    mf = tmp_path / "mapping.json"
    mf.write_text(json.dumps({"11-chapter.md": "07-chapter.md"}), encoding="utf-8")

    # Inline extends / overrides
    mapping = _resolve_mapping(mf, ["14-chapter.md:08-chapter.md"])
    assert mapping["11-chapter.md"] == "07-chapter.md"
    assert mapping["14-chapter.md"] == "08-chapter.md"

    # Collision
    with pytest.raises(ValueError):
        _resolve_mapping(mf, ["XX.md:07-chapter.md"])  # two targets -> 07-chapter.md


# ----------------------------
# Header & Anchor Normalization
# ----------------------------


def test_update_header_and_anchor_es(tmp_path: Path):
    f = tmp_path / "11-chapter.md"
    write_chapter(f, ES_H1)
    update_header_and_anchor(f, 7, lang="es", dry_run=False)
    out = f.read_text(encoding="utf-8")
    assert out.startswith("# ✦ Capítulo 7:"), out
    assert "{#-chapter-7}" in out


def test_update_header_and_anchor_de(tmp_path: Path):
    f = tmp_path / "09-chapter.md"
    write_chapter(f, DE_H1)
    update_header_and_anchor(f, 16, lang="de", dry_run=False)
    out = f.read_text(encoding="utf-8")
    assert out.startswith("# ✦ Kapitel 16:"), out
    assert "{#-chapter-16}" in out


def test_update_header_and_anchor_en_autodetect(tmp_path: Path):
    f = tmp_path / "07-chapter.md"
    write_chapter(f, EN_H1)
    # No lang provided -> autodetect EN from header
    update_header_and_anchor(f, 10, lang=None, dry_run=False)
    out = f.read_text(encoding="utf-8")
    assert out.startswith("# ✦ Chapter 10:"), out
    assert "{#-chapter-10}" in out


def test_update_header_anchor_fallback_anchor_only(tmp_path: Path):
    f = tmp_path / "16-chapter.md"
    write_chapter(f, ES_H1_NO_ANCHOR)
    # update should add anchor {#-chapter-9} and adjust number in H1
    update_header_and_anchor(f, 9, lang="es", dry_run=False)
    out = f.read_text(encoding="utf-8")
    assert out.startswith("# ✦ Capítulo 9:"), out
    assert "{#-chapter-9}" in out


# ----------------------------
# Two-Phase Rename
# ----------------------------


def test_two_phase_rename_and_header_update(tmp_path: Path):
    base = tmp_path / "manuscript" / "chapters"
    base.mkdir(parents=True, exist_ok=True)

    # Source files
    src_a = base / "11-chapter.md"
    src_b = base / "14-chapter.md"
    write_chapter(src_a, ES_H1)  # Capítulo 11
    write_chapter(src_b, ES_H1_NO_ANCHOR.replace("16", "14"))

    mapping = {
        "11-chapter.md": "07-chapter.md",
        "14-chapter.md": "08-chapter.md",
    }

    # Phase 1 + 2 (real run)
    _ = _two_phase_rename(base, mapping, dry_run=False)
    # Files should now be at targets
    tgt_a = base / "07-chapter.md"
    tgt_b = base / "08-chapter.md"
    assert tgt_a.exists(), "Target A missing"
    assert tgt_b.exists(), "Target B missing"

    # Update headers to match new numbers
    update_header_and_anchor(tgt_a, 7, lang="es", dry_run=False)
    update_header_and_anchor(tgt_b, 8, lang="es", dry_run=False)

    assert (base / "11-chapter.md").exists() is False
    out_a = tgt_a.read_text(encoding="utf-8")
    out_b = tgt_b.read_text(encoding="utf-8")
    assert out_a.startswith("# ✦ Capítulo 7:")
    assert "{#-chapter-7}" in out_a
    assert out_b.startswith("# ✦ Capítulo 8:")
    assert "{#-chapter-8}" in out_b


def test_two_phase_rename_dry_run(tmp_path: Path):
    base = tmp_path / "manuscript" / "chapters"
    base.mkdir(parents=True, exist_ok=True)

    src = base / "11-chapter.md"
    write_chapter(src, ES_H1)
    mapping = {"11-chapter.md": "07-chapter.md"}

    tmp_map = _two_phase_rename(base, mapping, dry_run=True)

    # In dry-run: no file changes should occur
    assert src.exists(), "Source should remain in dry-run"
    tgt = base / "07-chapter.md"
    assert not tgt.exists()

    # tmp_map still returns the intended paths (for logging), but nothing moved
    assert len(tmp_map) == 1
    (tmp_path_key, final_path) = list(tmp_map.items())[0]
    # tmp files not created on dry-run
    assert not tmp_path_key.exists()
    assert final_path.name == "07-chapter.md"


# ----------------------------
# Autodetect language
# ----------------------------


def test_autodetect_lang():
    assert autodetect_lang_by_header(ES_H1) == "es"
    assert autodetect_lang_by_header(DE_H1) == "de"
    assert autodetect_lang_by_header(EN_H1) == "en"
    assert autodetect_lang_by_header("no matching header") is None
