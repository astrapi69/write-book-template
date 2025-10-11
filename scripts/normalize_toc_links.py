# scripts/normalize_toc_links.py
import re
import argparse
from pathlib import Path


def strip_to_anchors(text: str) -> str:
    """
    Wandelt Links wie (chapters/01.md#einleitung) bzw. (chapters/01.gfm#einleitung)
    in reine Anker um: (#einleitung).
    Lässt reine Anker unverändert.
    """
    # (irgendwas).md|.gfm|.markdown#anchor  ->  (#anchor)
    pattern = re.compile(r"\((?:[^)\s]+)\.(?:md|gfm|markdown)(#[^)]+)\)")
    return pattern.sub(r"(\1)", text)


def replace_extension(text: str, ext: str) -> str:
    """
    Ersetzt Vorkommen von .gfm/.markdown/.md in Link-Zielen auf die gewünschte Endung.
    Beeinflusst NUR Links, nicht Freitext.
    """

    # nur in URL-Teilen innerhalb von (...) austauschen
    def repl(m):
        url = m.group(1)
        # tausche Endung am Ende oder vor #anchor
        url = re.sub(r"\.(?:md|gfm|markdown)(?=(?:\)|#))", f".{ext}", url)
        return f"({url})"

    return re.sub(r"\(([^)]+)\)", repl, text)


def main():
    ap = argparse.ArgumentParser(
        description="Normalize TOC links for single-file export."
    )
    ap.add_argument(
        "--toc", default="manuscript/front-matter/toc.md", help="Pfad zur TOC-Datei"
    )
    ap.add_argument(
        "--mode",
        choices=["strip-to-anchors", "replace-ext"],
        default="strip-to-anchors",
        help="Links zu reinen Ankern machen ODER nur Dateiendungen ersetzen",
    )
    ap.add_argument("--ext", default="md", help="Ziel-Endung, wenn mode=replace-ext")
    args = ap.parse_args()

    toc_path = Path(args.toc)
    if not toc_path.exists():
        print(f"⚠️  TOC not found: {toc_path}")
        return

    text = toc_path.read_text(encoding="utf-8")
    if args.mode == "strip-to-anchors":
        new_text = strip_to_anchors(text)
    else:
        new_text = replace_extension(text, args.ext)

    if new_text != text:
        toc_path.write_text(new_text, encoding="utf-8")
        print(f"✅ TOC normalized: {toc_path}")
    else:
        print(f"ℹ️  TOC unchanged (already normalized): {toc_path}")


if __name__ == "__main__":
    main()
