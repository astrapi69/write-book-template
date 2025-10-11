# tests/test_convert_to_absolute_fuzz.py
from pathlib import Path
import os
import string
import hypothesis.strategies as st
from hypothesis import given, settings, HealthCheck

from scripts.convert_to_absolute import convert_file_to_absolute


def write(p: Path, txt: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, encoding="utf-8")


# Strategy for sane labels and filenames
labels = st.text(
    alphabet=st.sampled_from(list(string.ascii_letters + string.digits + " -_")),
    min_size=1,
    max_size=20,
)
# Filenames that may include parentheses and spaces
filenames = st.builds(
    lambda base, ext: f"{base}{ext}",
    base=st.text(
        alphabet=st.sampled_from(list("ab cdefghijklmnop()_-")), min_size=1, max_size=12
    ),
    ext=st.sampled_from([".png", ".jpg", ".jpeg"]),
)


@given(labels, filenames)
@settings(
    deadline=None,
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_fuzz_relative_images_with_parentheses_and_spaces(
    tmp_path_factory, label: str, fname: str
):
    base = tmp_path_factory.mktemp("fuzzcase")
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "fuzz" / fname
    write(img, "x")

    md = ch / "doc.md"
    rel = os.path.relpath(img, start=md.parent)

    body = (
        f"![{label}]({rel})\n" f"![{label}](<{rel}>)\n" f'![{label}](<{rel}> "Cover")\n'
    )
    write(md, body)

    changed, count = convert_file_to_absolute(md)
    assert changed
    out = md.read_text(encoding="utf-8")
    assert str(img.resolve()) in out
    assert ' "Cover")' in out


def test_bare_url_with_parentheses_and_no_angle_brackets(tmp_path_factory):
    base = tmp_path_factory.mktemp("bareparen")
    ch = base / "manuscript" / "chapters"
    img = base / "assets" / "has(paren) and (space).png"
    write(img, "x")

    md = ch / "doc.md"
    rel = os.path.relpath(img, start=md.parent)
    write(md, f"![p]({rel})")

    changed, cnt = convert_file_to_absolute(md)
    assert changed and cnt == 1
    out = md.read_text(encoding="utf-8")
    assert f"![p]({img.resolve()})" in out


def test_title_single_or_double_quotes_following_bare_url(tmp_path_factory):
    base = tmp_path_factory.mktemp("titles")
    ch = base / "manuscript" / "chapters"
    img1 = base / "assets" / "t1(a).png"
    img2 = base / "assets" / "t2(b).png"
    write(img1, "x")
    write(img2, "x")

    md = ch / "doc.md"
    rel1 = os.path.relpath(img1, start=md.parent)
    rel2 = os.path.relpath(img2, start=md.parent)
    write(md, f"![x]({rel1} \"A\")\n![y]({rel2} 'B')")

    changed, cnt = convert_file_to_absolute(md)
    assert changed and cnt == 2
    out = md.read_text(encoding="utf-8")
    assert f'![x]({img1.resolve()} "A")' in out
    assert f"![y]({img2.resolve()} 'B')" in out
