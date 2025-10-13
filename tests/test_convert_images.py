# tests/test_convert_images.py
from pathlib import Path
import re
import pytest

from scripts.convert_images import convert_markdown_file, convert_markdown_dir

FIG_RE = re.compile(
    r'<figure(?:\s+class="[^"]+")?>\s*'
    r'<img\s+src="([^"]+)"\s+alt="([^"]+)"\s*/>\s*'
    r"<figcaption>\s*<em>(.*?)</em>\s*</figcaption>\s*"
    r"</figure>",
    re.DOTALL,
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# ---------- single-file tests ----------


def test_converts_simple_inline_image(tmp_path: Path):
    md = tmp_path / "a.md"
    write(md, "Hello ![Alt](img/cat.png) world.\n")

    n = convert_markdown_file(md)
    assert n == 1

    out = read(md)
    m = FIG_RE.search(out)
    assert m, f"Figure not found in:\n{out}"
    src, alt, caption = m.groups()
    assert src == "img/cat.png"
    assert alt == "Alt"
    assert caption == "Alt"


def test_uses_title_as_caption_when_present(tmp_path: Path):
    md = tmp_path / "t.md"
    write(md, '![Hund](pics/dog.jpg "Ein lieber Hund")\n')

    n = convert_markdown_file(md)
    assert n == 1
    out = read(md)
    m = FIG_RE.search(out)
    assert m is not None, f"no match in output:\n{out}"
    src, alt, caption = m.groups()
    assert src == "pics/dog.jpg"
    assert alt == "Hund"
    assert caption == "Ein lieber Hund"


@pytest.mark.parametrize(
    "wrapper", ["<pics/file with spaces.png>", "<../weird (1).png>"]
)
def test_angle_bracket_url_and_spaces_supported(tmp_path: Path, wrapper):
    md = tmp_path / "s.md"
    write(md, f'![X]({wrapper} "T")\n')

    n = convert_markdown_file(md)
    assert n == 1
    out = read(md)
    m = FIG_RE.search(out)
    assert m is not None, f"no match in output:\n{out}"
    src, alt, caption = m.groups()
    assert src == wrapper[1:-1]
    assert alt == "X"
    assert caption == "T"


def test_skips_fenced_code_blocks(tmp_path: Path):
    md = tmp_path / "code.md"
    write(md, "Before\n" "```\n" '![ALT](img/in_code.png "T")\n' "```\n" "After\n")
    n = convert_markdown_file(md)
    assert n == 0
    assert read(md).count("![ALT](") == 1


def test_skips_inline_code_spans(tmp_path: Path):
    md = tmp_path / "inline.md"
    write(md, 'Text `![ALT](path/x.png "T")` Text\n')

    n = convert_markdown_file(md)
    assert n == 0
    assert read(md).count("![ALT](") == 1


def test_reference_style_images_are_resolved(tmp_path: Path):
    md = tmp_path / "ref.md"
    write(md, "Here: ![Logo][app]\n" '[app]: assets/logo.svg "Brand"\n')

    n = convert_markdown_file(md)
    assert n == 1
    out = read(md)
    m = FIG_RE.search(out)
    assert m is not None, f"no match in output:\n{out}"
    src, alt, caption = m.groups()
    assert src == "assets/logo.svg"
    assert alt == "Logo"
    assert caption == "Brand"


def test_reference_empty_id_uses_alt_as_key(tmp_path: Path):
    md = tmp_path / "ref2.md"
    write(md, "An image: ![Foo][]\n" '[foo]: img/foo.png "Titel Foo"\n')
    n = convert_markdown_file(md)
    assert n == 1
    out = read(md)
    m = FIG_RE.search(out)
    assert m is not None, f"no match in output:\n{out}"
    src, alt, caption = m.groups()
    assert src == "img/foo.png"
    assert alt == "Foo"
    assert caption == "Titel Foo"


def test_unknown_reference_is_left_untouched(tmp_path: Path):
    md = tmp_path / "ref3.md"
    write(md, "Oops: ![Bar][missing]\n")

    n = convert_markdown_file(md)
    assert n == 0
    assert read(md) == "Oops: ![Bar][missing]\n"


def test_default_is_no_backup(tmp_path: Path):
    md = tmp_path / "nb.md"
    write(md, "![A](x.png)\n")
    n = convert_markdown_file(md)  # default: backup=False
    assert n == 1
    assert not md.with_suffix(".md.bak").exists()


def test_backup_when_enabled(tmp_path: Path):
    md = tmp_path / "b.md"
    write(md, "![A](x.png)\n")
    bak = md.with_suffix(".md.bak")
    assert not bak.exists()

    n = convert_markdown_file(md, backup=True)
    assert n == 1
    assert bak.exists()
    assert read(bak) == "![A](x.png)\n"  # original preserved in backup


def test_dry_run_writes_nothing(tmp_path: Path):
    md = tmp_path / "dry.md"
    before = "Start ![A](x.png) End\n"
    write(md, before)

    n = convert_markdown_file(md, dry_run=True)
    assert n == 1
    assert read(md) == before
    assert not md.with_suffix(".md.bak").exists()


def test_applies_figure_class_when_provided(tmp_path: Path):
    md = tmp_path / "cls.md"
    write(md, "![A](x.png)\n")

    n = convert_markdown_file(md, figure_class="img-figure")
    assert n == 1
    out = read(md)
    assert '<figure class="img-figure">' in out


def test_file_not_found_returns_zero(tmp_path: Path):
    missing = tmp_path / "nope.md"
    n = convert_markdown_file(missing)
    assert n == 0


def test_no_images_no_change(tmp_path: Path):
    md = tmp_path / "plain.md"
    write(md, "No image here.\n")
    n = convert_markdown_file(md)
    assert n == 0
    assert read(md) == "No image here.\n"


# ---------- directory (recursive) tests ----------


def test_directory_recursive_conversion(tmp_path: Path):
    sub = tmp_path / "chapter1" / "images"
    sub.mkdir(parents=True)
    f1 = tmp_path / "root.md"
    f2 = sub / "nested.md"

    write(f1, "Intro ![A](a.png)")
    write(f2, "Nested ![B](b.png)")

    total = convert_markdown_dir(tmp_path)  # default: no backups
    assert total == 2

    assert FIG_RE.search(read(f1))
    assert FIG_RE.search(read(f2))


def test_dry_run_directory(tmp_path: Path):
    sub = tmp_path / "part"
    sub.mkdir()
    f = sub / "c.md"
    write(f, "![Alt](c.png)")

    total = convert_markdown_dir(tmp_path, dry_run=True)
    assert total == 1
    # original file unchanged
    assert "![Alt](" in read(f)
