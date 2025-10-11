# tests/test_full_export_book.py
import pytest
import os
import shutil
from pathlib import Path
import subprocess
from unittest.mock import patch, ANY
from scripts.full_export_book import prepare_output_folder, run_script, compile_book

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

    # Act
    compile_book("pdf", ["chapters"])

    # Assert
    mock_run.assert_called()
