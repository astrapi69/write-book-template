#!/usr/bin/env python3
# scripts/pandoc_batch.py
from __future__ import annotations

import argparse
import os
import shutil
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import tempfile
from typing import Optional, Tuple, Dict, List

# --- TOML loader (tomllib for 3.11+, fallback to toml) ---
try:
    import tomllib as _toml  # Python 3.11+

    def load_toml(p: Path) -> dict:
        return _toml.loads(p.read_text(encoding="utf-8"))

except Exception:
    try:
        import toml as _toml  # type: ignore

        def load_toml(p: Path) -> dict:
            return _toml.load(p)  # type: ignore

    except Exception:
        _toml = None  # type: ignore

        def load_toml(p: Path) -> dict:
            return {}


EXT_BY_TO: Dict[str, str] = {
    "epub": ".epub",
    "html": ".html",
    "pdf": ".pdf",
    "docx": ".docx",
    "odt": ".odt",
    "rtf": ".rtf",
}

# Horizontal rule regex; ensure a blank line after HR if the next line is not blank.
HRX = re.compile(r"(?m)^(?:-{3}|(?:\*\s*){3}|(?:_\s*){3})[ \t]*\r?\n(?![ \t]*\r?\n)")


def patch_markdown_text(text: str) -> Tuple[str, int]:
    """
    Patch markdown:
      - strip UTF-8 BOM
      - normalize newlines to '\n'
      - ensure a blank line after HR if next line is not blank
    Returns (patched_text, num_replacements).
    """
    if text.startswith("\ufeff"):
        text = text[1:]
    # Normalize line endings cheaply.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    patched, n1 = HRX.subn(lambda m: m.group(0) + "\n", text)
    return patched, n1


def require_cmd(cmd: str) -> None:
    if shutil.which(cmd) is None:
        print(f"ERROR: '{cmd}' not found in PATH.", file=sys.stderr)
        sys.exit(127)


def find_pyproject() -> Optional[Path]:
    # Search from CWD upwards
    for p in [Path.cwd(), *Path.cwd().parents]:
        f = p / "pyproject.toml"
        if f.exists():
            return f
    # Fallback: search from script location upwards
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents]:
        f = p / "pyproject.toml"
        if f.exists():
            return f
    return None


def load_defaults() -> dict:
    pp = find_pyproject()
    if not pp or _toml is None:
        return {}
    try:
        data = load_toml(pp)
    except Exception:
        return {}
    return data.get("tool", {}).get("pandoc_batch", {}) or {}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    defaults = load_defaults()

    p = argparse.ArgumentParser(
        description="Batch Pandoc conversion for all .md files in a directory tree."
    )
    p.add_argument(
        "--root",
        type=Path,
        default=Path(defaults.get("root", "manuscript")),
        help="Root folder to search for .md files (recursively).",
    )
    p.add_argument(
        "--outdir",
        type=Path,
        default=Path(defaults.get("outdir", "output")),
        help="Output folder (directory structure is mirrored).",
    )
    p.add_argument(
        "--to",
        choices=list(EXT_BY_TO.keys()),
        default=defaults.get("to"),
        help="Pandoc output format.",
    )
    p.add_argument(
        "--from",
        dest="from_fmt",
        default=defaults.get("from", "markdown"),
        help="Pandoc --from format (default: markdown).",
    )
    p.add_argument(
        "--metadata-file",
        type=Path,
        default=defaults.get("metadata_file"),
        help="Path to a YAML metadata file.",
    )
    p.add_argument(
        "--resource-path",
        action="append",
        default=defaults.get("resource_path", []),
        help="Resource path(s); may be passed multiple times.",
    )
    p.add_argument(
        "--lang",
        default=defaults.get("lang"),
        help="--metadata lang=<code> passed to Pandoc.",
    )
    p.add_argument(
        "--standalone",
        action="store_true",
        default=defaults.get("standalone", True),
        help="Pass --standalone to Pandoc (default: on). Use --no-standalone to disable.",
    )
    p.add_argument("--no-standalone", dest="standalone", action="store_false")
    p.add_argument(
        "--verbose",
        action="store_true",
        default=defaults.get("verbose", False),
        help="Pass --verbose to Pandoc.",
    )
    p.add_argument(
        "--jobs",
        type=int,
        default=defaults.get("jobs", os.cpu_count() or 4),
        help="Parallel jobs.",
    )
    p.add_argument(
        "--test-only",
        action="store_true",
        default=defaults.get("test_only", False),
        help="Don’t write files; output -> os.devnull.",
    )
    p.add_argument(
        "--extra", nargs=argparse.REMAINDER, help="Extra Pandoc args after '--'."
    )
    p.add_argument(
        "--print-config", action="store_true", help="Print resolved config and exit."
    )
    p.add_argument(
        "--patch-md",
        action="store_true",
        default=True,
        help="Pre-patch markdown (strip BOM, normalize newlines, blank line after HR). Default: on.",
    )
    p.add_argument(
        "--no-patch-md",
        dest="patch_md",
        action="store_false",
        help="Disable pre-patching.",
    )
    p.add_argument(
        "--fix-inplace",
        action="store_true",
        help="Write patched markdown back to source files (in-place).",
    )
    p.add_argument(
        "--report-patches",
        action="store_true",
        help="Print how many fixes were applied per file.",
    )

    args = p.parse_args(argv)

    if args.print_config:
        print("Resolved config:")
        for k, v in vars(args).items():
            if k not in {"extra", "print_config"}:
                print(f"  {k}: {v}")
        sys.exit(0)

    if not args.to:
        p.error(
            "--to is required (either pass it or set it under [tool.pandoc_batch] in pyproject.toml)"
        )
    return args


def rel_output_path(src: Path, root: Path, outdir: Path, ext: str) -> Path:
    rel = src.relative_to(root)
    return (outdir / rel).with_suffix(ext)


def build_cmd(
    infile: Path, outfile: Optional[Path], args: argparse.Namespace
) -> List[str]:
    cmd: List[str] = ["pandoc"]
    if args.verbose:
        cmd.append("--verbose")
    if args.standalone:
        cmd.append("--standalone")
    cmd += ["--from", args.from_fmt, "--to", args.to]
    if args.metadata_file:
        cmd += ["--metadata-file", str(args.metadata_file)]
    if args.lang:
        cmd += ["--metadata", f"lang={args.lang}"]
    if args.resource_path:
        sep = ";" if os.name == "nt" else ":"
        cmd += ["--resource-path", sep.join(args.resource_path)]
    cmd += ["--output", os.devnull if outfile is None else str(outfile)]
    cmd.append(str(infile))
    if args.extra:
        cmd += args.extra
    return cmd


def _create_temp_with(patched: str) -> Path:
    # Separate helper to simplify testing & ensure cleanup paths are predictable.
    tf = tempfile.NamedTemporaryFile(prefix="pandoc_patch_", suffix=".md", delete=False)
    try:
        tf.write(patched.encode("utf-8"))
        tf.flush()
        name = tf.name
    finally:
        tf.close()
    return Path(name)


def run_one(
    infile: Path, outfile: Optional[Path], args: argparse.Namespace
) -> Tuple[Path, int, str]:
    # Ensure parent dir for output exists (even if test-only, keep behavior uniform)
    if outfile is not None:
        outfile.parent.mkdir(parents=True, exist_ok=True)

    input_path_for_pandoc = infile

    if args.patch_md:
        raw = infile.read_text(encoding="utf-8", errors="strict")
        patched, fixes = patch_markdown_text(raw)

        if args.report_patches:
            print(f"[PATCH] {infile}: {fixes} fix(es)")

        if args.fix_inplace:
            if patched != raw:
                infile.write_text(patched, encoding="utf-8")
        else:
            input_path_for_pandoc = _create_temp_with(patched)

    cmd = build_cmd(input_path_for_pandoc, outfile, args)
    proc = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up temp file if we made one
    if args.patch_md and not args.fix_inplace and input_path_for_pandoc != infile:
        try:
            input_path_for_pandoc.unlink(missing_ok=True)
        except Exception:
            pass

    rc = proc.returncode
    # Keep tails small to avoid huge buffers on large runs
    stdout_tail = (proc.stdout or "")[-1000:]
    stderr_tail = (proc.stderr or "")[-2000:]
    log = stdout_tail + ("\n" if stdout_tail and stderr_tail else "") + stderr_tail
    return infile, rc, log


def main(argv: Optional[List[str]] = None) -> None:
    require_cmd("pandoc")
    args = parse_args(argv)

    root = args.root.resolve()
    outdir = args.outdir.resolve()
    ext = EXT_BY_TO[args.to]

    files = sorted(root.rglob("*.md"))
    if not files:
        print(f"No .md files found under {root}", file=sys.stderr)
        sys.exit(2)

    tasks = [
        (f, None if args.test_only else rel_output_path(f, root, outdir, ext))
        for f in files
    ]

    failures = 0
    print(
        f"Starting Pandoc for {len(tasks)} file(s), format: {args.to}, jobs: {args.jobs}..."
    )
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        futs = {ex.submit(run_one, f, o, args): (f, o) for f, o in tasks}
        for fut in as_completed(futs):
            infile, outfile = futs[fut]
            inf, rc, log = fut.result()
            tag = "OK" if rc == 0 else "FAIL"
            print(f"[{tag}] {inf}{' -> ' + str(outfile) if outfile else ''}")
            if args.verbose or rc != 0:
                if log.strip():
                    print(log.strip())
            if rc != 0:
                failures += 1

    if failures:
        print(f"\nDONE with {failures} failure(s).", file=sys.stderr)
        sys.exit(1)
    print("\nDONE without errors.")
    sys.exit(0)


if __name__ == "__main__":
    main()
