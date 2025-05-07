import pytest
import os
import shutil
import subprocess
from unittest.mock import patch, ANY
from scripts.full_export_book import prepare_output_folder, run_script, compile_book

# Define test dirs
TEST_OUTPUT_DIR = "test_output"
TEST_BACKUP_DIR = "test_output_backup"


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """ Setup and cleanup test directories before and after tests """
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)  # ✅ Always create test_output/
    os.makedirs(TEST_BACKUP_DIR, exist_ok=True)  # ✅ Always create test_output_backup/

    yield  # Run the tests

    # ✅ Cleanup after tests
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    if os.path.exists(TEST_BACKUP_DIR):
        shutil.rmtree(TEST_BACKUP_DIR)


@patch("subprocess.run")
def test_run_script_success(mock_run):
    """Test running a script without errors"""
    mock_run.return_value.returncode = 0
    run_script("scripts/convert_to_absolute.py")
    mock_run.assert_called_with(["python3", "scripts/convert_to_absolute.py"], check=True, stdout=ANY, stderr=ANY)


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
def test_run_script_failure(mock_run):
    """Test handling errors when running a script"""
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

    # Output folder should have been moved to backup
    assert not os.path.exists(TEST_OUTPUT_DIR)
    assert os.path.exists(TEST_BACKUP_DIR)
    assert os.path.exists(os.path.join(TEST_BACKUP_DIR, "dummy.md"))


@patch("subprocess.run")
@patch("scripts.full_export_book.BOOK_DIR", "tests/fixtures/manuscript")  # Assumes you have fixture .md files
@patch("scripts.full_export_book.OUTPUT_DIR", TEST_OUTPUT_DIR)
@patch("scripts.full_export_book.METADATA_FILE", "tests/fixtures/metadata.yaml")
def test_compile_book(mock_run):
    """Test compiling book using mocked environment"""
    # Ensure dummy environment
    os.makedirs("tests/fixtures/manuscript/chapters", exist_ok=True)
    md_path = "tests/fixtures/manuscript/chapters/test.md"
    with open(md_path, "w") as f:
        f.write("# Test")

    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname("tests/fixtures/metadata.yaml"), exist_ok=True)
    with open("tests/fixtures/metadata.yaml", "w") as f:
        f.write("title: Test\n")

    compile_book("pdf", ["chapters"])

    mock_run.assert_called()
