# tests/test_normalize_toc_links.py
import sys
import subprocess
from pathlib import Path

# Resolve the real repository root as two levels up from this test file
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "normalize_toc_links.py"


def run_script(toc_path: Path, args):
    assert SCRIPT_PATH.exists(), f"normalize_toc_links.py not found at {SCRIPT_PATH}"
    cmd = [sys.executable, str(SCRIPT_PATH), "--toc", str(toc_path), *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),  # run from repo root for stable relative imports (if any)
        check=False,
    )


def test_strip_to_anchors_basic(tmp_path):
    # Create a temp TOC in tmp_path
    toc = tmp_path / "toc.md"
    toc.write_text(
        "\n".join(
            [
                "- [Intro](chapters/01.gfm#einleitung)",
                "- [Kapitel 2](chapters/02.markdown#zweites)",
                "- [Schon Anker](#bereits-anker)",
                "- [Normales .md](chapters/03.md#drittes)",
            ]
        ),
        encoding="utf-8",
    )

    res = run_script(toc, ["--mode", "strip-to-anchors"])
    assert res.returncode == 0, res.stderr

    out = toc.read_text(encoding="utf-8")
    assert "(#einleitung)" in out
    assert "(#zweites)" in out
    assert "(#bereits-anker)" in out  # unchanged
    assert "(#drittes)" in out
    # ensure file paths are stripped
    assert "chapters/01.gfm" not in out
    assert "chapters/02.markdown" not in out
    assert "chapters/03.md" not in out


def test_replace_ext_swaps_endings(tmp_path):
    toc = tmp_path / "toc.md"
    toc.write_text(
        "\n".join(
            [
                "- [GFM](chapters/01.gfm#einleitung)",
                "- [MD](chapters/02.md#zweites)",
                "- [MARKDOWN](chapters/03.markdown#drittes)",
                "- [Nur Anker](#nur-anker)",  # should stay unchanged
            ]
        ),
        encoding="utf-8",
    )

    res = run_script(toc, ["--mode", "replace-ext", "--ext", "md"])
    assert res.returncode == 0, res.stderr

    out = toc.read_text(encoding="utf-8")
    assert "(chapters/01.md#einleitung)" in out
    assert "(chapters/02.md#zweites)" in out
    assert "(chapters/03.md#drittes)" in out
    assert "(#nur-anker)" in out  # untouched


def test_strip_to_anchors_idempotent(tmp_path):
    toc = tmp_path / "toc.md"
    toc.write_text(
        "- [Intro](chapters/01.gfm#einleitung)\n- [Anchor](#x)",
        encoding="utf-8",
    )

    res1 = run_script(toc, ["--mode", "strip-to-anchors"])
    assert res1.returncode == 0, res1.stderr
    first = toc.read_text(encoding="utf-8")

    res2 = run_script(toc, ["--mode", "strip-to-anchors"])
    assert res2.returncode == 0, res2.stderr
    second = toc.read_text(encoding="utf-8")

    assert first == second, "strip-to-anchors should be idempotent"
