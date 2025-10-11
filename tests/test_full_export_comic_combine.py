# tests/test_full_export_comic_combine.py
from pathlib import Path

import scripts.full_export_comic as fec


def write_html(p: Path, head: str, body: str):
    p.write_text(
        f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{p.stem}</title>
{head}
</head>
<body>
{body}
</body>
</html>
""",
        encoding="utf-8",
    )


def test_combines_html_extracts_bodies(tmp_path: Path):
    chapters = tmp_path / "chapters"
    outdir = tmp_path / "out"
    chapters.mkdir()

    write_html(chapters / "01-einleitung.html", "<!-- head1 -->", "<h1>Intro</h1>")
    write_html(chapters / "02-abenteuer.html", "<!-- head2 -->", "<p>Story</p>")

    output_html = outdir / "book.html"
    included = fec.combine_html_chapters(
        chapter_dir=str(chapters),
        output_file=str(output_html),
        title="Die Nasenbohrer-Chroniken",
        lang="de",
        stylesheet_path="config/comic.css",
    )

    assert [p.name for p in included] == ["01-einleitung.html", "02-abenteuer.html"]
    text = output_html.read_text(encoding="utf-8")
    # head basics
    assert '<html lang="de">' in text
    assert "<meta charset=" in text
    assert "<title>Die Nasenbohrer-Chroniken</title>" in text
    assert 'rel="stylesheet" href="config/comic.css"' in text
    # body merged in correct order with markers
    assert text.index("<!-- BEGIN 01-einleitung.html -->") < text.index(
        "<!-- BEGIN 02-abenteuer.html -->"
    )
    assert "<h1>Intro</h1>" in text and "<p>Story</p>" in text


def test_sorting_by_numeric_prefix_then_name(tmp_path: Path):
    c = tmp_path / "chapters"
    c.mkdir()
    # Should sort: 01-..., 2-..., then non-numeric by name
    for name in ["2-zwei.html", "z-omega.html", "01-eins.html", "a-alpha.html"]:
        (c / name).write_text("<body>ok</body>", encoding="utf-8")

    out = tmp_path / "out/book.html"
    included = fec.combine_html_chapters(str(c), str(out))
    assert [p.name for p in included] == [
        "01-eins.html",
        "2-zwei.html",
        "a-alpha.html",
        "z-omega.html",
    ]


def test_includes_whole_file_when_no_body(tmp_path: Path):
    c = tmp_path / "chapters"
    c.mkdir()
    (c / "01-x.html").write_text("<h1>No body tag here</h1>", encoding="utf-8")

    out = tmp_path / "out/book.html"
    fec.combine_html_chapters(str(c), str(out))
    text = out.read_text(encoding="utf-8")
    assert "No body tag here" in text


def test_raises_when_no_html_or_missing_dir(tmp_path: Path):
    # missing dir
    missing = tmp_path / "nope"
    out = tmp_path / "out/book.html"
    try:
        fec.combine_html_chapters(str(missing), str(out))
        assert False, "expected FileNotFoundError for missing dir"
    except FileNotFoundError:
        pass

    # empty dir
    empty = tmp_path / "empty"
    empty.mkdir()
    try:
        fec.combine_html_chapters(str(empty), str(out))
        assert False, "expected FileNotFoundError for empty dir"
    except FileNotFoundError:
        pass
