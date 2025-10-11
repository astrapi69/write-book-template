# tests/test_pandoc_batch_cmd_and_paths.py
from pathlib import Path
from scripts.pandoc_batch import build_cmd, rel_output_path, EXT_BY_TO
import argparse
import os


def _ns(**kw):
    # Minimal argparse.Namespace for build_cmd
    return argparse.Namespace(
        **{
            "verbose": False,
            "standalone": True,
            "from_fmt": "markdown",
            "to": "html",
            "metadata_file": None,
            "lang": "de",
            "resource_path": [],
            "extra": None,
        }
        | kw
    )


def test_rel_output_path_maps_structure(tmp_path: Path):
    root = tmp_path / "root"
    src = root / "a" / "b" / "c.md"
    src.parent.mkdir(parents=True)
    src.write_text("# hi", encoding="utf-8")
    outdir = tmp_path / "out"
    p = rel_output_path(src, root, outdir, EXT_BY_TO["html"])
    assert p == outdir / "a" / "b" / "c.html"


def test_build_cmd_basic(tmp_path: Path):
    infile = tmp_path / "x.md"
    infile.write_text("x", encoding="utf-8")
    outfile = tmp_path / "y.html"
    args = _ns()
    cmd = build_cmd(infile, outfile, args)
    assert cmd[0] == "pandoc"
    assert "--standalone" in cmd
    assert ["--from", "markdown"] == cmd[cmd.index("--from") : cmd.index("--from") + 2]
    assert ["--to", "html"] == cmd[cmd.index("--to") : cmd.index("--to") + 2]
    assert ["--output", str(outfile)] in [cmd[i : i + 2] for i in range(len(cmd) - 1)]
    assert str(infile) == cmd[-1]


def test_build_cmd_resource_paths_and_extra(tmp_path: Path):
    infile = tmp_path / "x.md"
    infile.write_text("x", encoding="utf-8")
    args = _ns(resource_path=["a", "b"], extra=["--toc", "--css", "style.css"])
    cmd = build_cmd(infile, None, args)
    sep = ";" if os.name == "nt" else ":"
    assert "--resource-path" in cmd
    rp = cmd[cmd.index("--resource-path") + 1]
    assert rp == sep.join(["a", "b"])
    assert cmd[-3:] == ["--toc", "--css", "style.css"]
