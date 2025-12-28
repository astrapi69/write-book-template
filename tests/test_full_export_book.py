# tests/test_full_export_book.py
import pytest
import os
import shutil
from pathlib import Path
import subprocess
from unittest.mock import patch, ANY
from scripts.full_export_book import prepare_output_folder, run_script, compile_book
from scripts.enums.book_type import BookType

TEST_OUTPUT_DIR = "test_output"
TEST_BACKUP_DIR = "test_output_backup"


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    # Clean start
    for p in (TEST_OUTPUT_DIR, TEST_BACKUP_DIR):
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEST_BACKUP_DIR, exist_ok=True)
    yield
    # Cleanup
    for p in (TEST_OUTPUT_DIR, TEST_BACKUP_DIR, "tests/fixtures"):
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)


@patch("subprocess.run")
def test_run_script_success(mock_run):
    mock_run.return_value.returncode = 0
    run_script("scripts/convert_to_absolute.py")
    mock_run.assert_called_with(
        ["python3", "scripts/convert_to_absolute.py"],
        check=True,
        stdout=ANY,
        stderr=ANY,
    )


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
def test_run_script_failure(mock_run):
    with pytest.raises(subprocess.CalledProcessError):
        run_script("scripts/convert_to_absolute.py")


@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.BACKUP_DIR", TEST_BACKUP_DIR)
def test_prepare_output_folder():
    """Test backup logic in prepare_output_folder"""
    # Write dummy file to simulate content
    dummy_file = os.path.join(TEST_OUTPUT_DIR, "dummy.md")
    with open(dummy_file, "w") as f:
        f.write("# Dummy")

    prepare_output_folder()

    # Output folder has been emptied/recreated
    assert os.path.exists(TEST_OUTPUT_DIR)
    assert not os.path.exists(os.path.join(TEST_OUTPUT_DIR, "dummy.md"))

    # Backup exists and contains the old file
    assert os.path.exists(TEST_BACKUP_DIR)
    assert os.path.exists(os.path.join(TEST_BACKUP_DIR, "dummy.md"))


@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.BACKUP_DIR", TEST_BACKUP_DIR)
def test_prepare_output_folder_moves_and_recreates_output():
    # Arrange: create output/ with a file
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    dummy = Path(TEST_OUTPUT_DIR) / "dummy.md"
    dummy.write_text("# Dummy", encoding="utf-8")

    # Act
    prepare_output_folder()

    # Assert: backup exists and contains the moved file (directly, no subfolder)
    assert os.path.isdir(TEST_BACKUP_DIR)
    assert (Path(TEST_BACKUP_DIR) / "dummy.md").exists()

    # Assert: output/ exists again and is empty
    assert os.path.isdir(TEST_OUTPUT_DIR)
    assert not any(
        Path(TEST_OUTPUT_DIR).iterdir()
    ), "OUTPUT_DIR should be recreated empty"


@patch("subprocess.run")
@patch("scripts.full_export_book.BOOK_DIR", "tests/fixtures/manuscript")
@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.METADATA_FILE", "tests/fixtures/metadata.yaml")
def test_compile_book(mock_run):
    # Arrange fixtures
    Path("tests/fixtures/manuscript/chapters").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/manuscript/chapters/test.md").write_text(
        "# Test", encoding="utf-8"
    )
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/metadata.yaml").write_text("title: Test\n", encoding="utf-8")

    # Act - now with required book_type argument
    compile_book("pdf", ["chapters"], BookType.EBOOK)

    # Assert
    mock_run.assert_called()


@patch("subprocess.run")
@patch("scripts.full_export_book.BOOK_DIR", "tests/fixtures/manuscript")
@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.METADATA_FILE", "tests/fixtures/metadata.yaml")
def test_compile_book_epub_skips_toc(mock_run):
    """Test that EPUB compilation skips manual TOC files"""
    # Arrange fixtures
    Path("tests/fixtures/manuscript/front-matter").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/manuscript/chapters").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/manuscript/front-matter/toc.md").write_text(
        "# TOC\n- [Chapter 1](#chapter-1)", encoding="utf-8"
    )
    Path("tests/fixtures/manuscript/chapters/test.md").write_text(
        "# Test", encoding="utf-8"
    )
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/metadata.yaml").write_text("title: Test\n", encoding="utf-8")

    # Act - compile EPUB with section order that includes toc.md
    compile_book(
        "epub",
        ["front-matter/toc.md", "chapters"],
        BookType.EBOOK,
    )

    # Assert - Pandoc should be called with --toc flag for auto-generation
    mock_run.assert_called()
    call_args = mock_run.call_args[0][0]
    assert "--toc" in call_args, "EPUB should have --toc flag for auto-generation"
    assert "--epub-chapter-level=1" in call_args


@patch("subprocess.run")
@patch("scripts.full_export_book.BOOK_DIR", "tests/fixtures/manuscript")
@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.METADATA_FILE", "tests/fixtures/metadata.yaml")
def test_compile_book_print_pdf_with_toc(mock_run):
    """Test that print PDF (paperback) generates TOC with page numbers"""
    # Arrange fixtures
    Path("tests/fixtures/manuscript/chapters").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/manuscript/chapters/test.md").write_text(
        "# Test", encoding="utf-8"
    )
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/metadata.yaml").write_text("title: Test\n", encoding="utf-8")

    # Act - compile PDF with paperback book type
    compile_book("pdf", ["chapters"], BookType.PAPERBACK)

    # Assert - Pandoc should be called with --toc flag for print PDF
    mock_run.assert_called()
    call_args = mock_run.call_args[0][0]
    assert "--toc" in call_args, "Print PDF should have --toc flag"
    assert "--pdf-engine=lualatex" in call_args


@patch("subprocess.run")
@patch("scripts.full_export_book.BOOK_DIR", "tests/fixtures/manuscript")
@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.METADATA_FILE", "tests/fixtures/metadata.yaml")
def test_compile_book_ebook_pdf_no_auto_toc(mock_run):
    """Test that ebook PDF does NOT auto-generate TOC (uses manual TOC)"""
    # Arrange fixtures
    Path("tests/fixtures/manuscript/chapters").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/manuscript/chapters/test.md").write_text(
        "# Test", encoding="utf-8"
    )
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/metadata.yaml").write_text("title: Test\n", encoding="utf-8")

    # Act - compile PDF with ebook book type (not paperback/hardcover)
    compile_book("pdf", ["chapters"], BookType.EBOOK)

    # Assert - Pandoc should NOT have --toc flag for ebook PDF
    mock_run.assert_called()
    call_args = mock_run.call_args[0][0]
    assert "--toc" not in call_args, "Ebook PDF should NOT have --toc flag"


@patch("subprocess.run")
@patch("scripts.full_export_book.BOOK_DIR", "tests/fixtures/manuscript")
@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.METADATA_FILE", "tests/fixtures/metadata.yaml")
def test_compile_book_custom_toc_depth(mock_run):
    """Test that custom TOC depth is passed to Pandoc"""
    # Arrange fixtures
    Path("tests/fixtures/manuscript/chapters").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/manuscript/chapters/test.md").write_text(
        "# Test", encoding="utf-8"
    )
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/metadata.yaml").write_text("title: Test\n", encoding="utf-8")

    # Act - compile EPUB with custom TOC depth
    compile_book("epub", ["chapters"], BookType.EBOOK, toc_depth=3)

    # Assert - Pandoc should have --toc-depth=3
    mock_run.assert_called()
    call_args = mock_run.call_args[0][0]
    assert "--toc-depth=3" in call_args, "Custom TOC depth should be passed to Pandoc"
