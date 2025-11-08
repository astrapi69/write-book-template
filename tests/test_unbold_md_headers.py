# tests/test_unbold_md_headers.py
from pathlib import Path

import pytest

import scripts.unbold_md_headers as m


def write(p: Path, text: str, enc: str = "utf-8"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding=enc)
    return p


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_header_bold_removed_only_in_headers(tmp_path: Path):
    src = """# **Main Title**
Some paragraph with **bold** should stay bold.
### **From Paper to Practice**
End.
"""
    expected = """# Main Title
Some paragraph with **bold** should stay bold.
### From Paper to Practice
End.
"""
    f = write(tmp_path / "doc.md", src)
    changes, wrote = m.process_file(f, allowed_levels=None, dry_run=False, backup=True)
    assert changes == 2
    assert wrote is True
    assert read(f) == expected

    # Backup created and equals original
    bak = f.with_suffix(".md.bak")
    assert bak.exists()
    assert read(bak) == src


def test_levels_filter_only_h3_changes(tmp_path: Path):
    src = """## **Keep Bold** (H2)
### **Change Me** (H3)
#### **Also Change Me** (H4)
"""
    expected = """## **Keep Bold** (H2)
### Change Me (H3)
#### Also Change Me (H4)
"""
    f = write(tmp_path / "doc.md", src)
    # Only levels 3 and 4
    changes, wrote = m.process_file(
        f, allowed_levels={3, 4}, dry_run=False, backup=False
    )
    assert changes == 2
    assert wrote is True
    assert read(f) == expected


def test_recursive_and_extensions(tmp_path: Path):
    # Create .mdx in subdir and .md in root
    mdx = write(tmp_path / "a/b/c.mdx", "### **MDX Title**\n")
    md = write(tmp_path / "root.md", "### **MD Title**\n")

    files = list(m.iter_files([tmp_path], recursive=True, ext=(".md", ".mdx")))
    # Both should be found
    assert set(p.suffix for p in files) == {".md", ".mdx"}

    # Process both
    total_changes = 0
    for p in files:
        ch, wrote = m.process_file(p, allowed_levels=None, dry_run=False, backup=False)
        assert wrote is True
        total_changes += ch

    assert total_changes == 2
    assert read(mdx) == "### MDX Title\n"
    assert read(md) == "### MD Title\n"


def test_dry_run_reports_but_does_not_write(
    tmp_path: Path, capsys: pytest.CaptureFixture
):
    src = "### **X**\n"
    f = write(tmp_path / "doc.md", src)
    changes, wrote = m.process_file(f, allowed_levels=None, dry_run=True, backup=True)
    assert changes == 1
    assert wrote is False
    # File unchanged
    assert read(f) == src


def test_no_backup_when_disabled(tmp_path: Path):
    f = write(tmp_path / "doc.md", "### **Title**\n")
    changes, wrote = m.process_file(f, allowed_levels=None, dry_run=False, backup=False)
    assert changes == 1 and wrote is True
    assert not (tmp_path / "doc.md.bak").exists()


def test_no_change_when_no_bold_in_header(tmp_path: Path):
    f = write(tmp_path / "doc.md", "### Title\nParagraph **bold** stays.\n")
    changes, wrote = m.process_file(f, allowed_levels=None, dry_run=False, backup=True)
    assert changes == 0
    assert wrote is False
    assert read(f) == "### Title\nParagraph **bold** stays.\n"


def test_trailing_text_after_bold_is_preserved(tmp_path: Path):
    f = write(tmp_path / "doc.md", "### **Title** with suffix\n")
    changes, wrote = m.process_file(f, allowed_levels=None, dry_run=False, backup=False)
    assert changes == 1 and wrote is True
    assert read(f) == "### Title with suffix\n"


@pytest.mark.parametrize(
    "levels,header,should_change",
    [
        ({1}, "# **A**\n", True),
        ({2}, "## **A**\n", True),
        ({3}, "### **A**\n", True),
        ({4}, "### **A**\n", False),
        (None, "###### **A**\n", True),
    ],
)
def test_levels_parametrized(tmp_path: Path, levels, header, should_change):
    f = write(tmp_path / "doc.md", header)
    changes, wrote = m.process_file(
        f, allowed_levels=levels, dry_run=False, backup=False
    )
    assert (changes > 0) == should_change
    assert wrote == should_change
