import pytest
import os
import shutil
import subprocess
from unittest.mock import patch
from scripts.full_export_book import prepare_output_folder, run_script, compile_book

from unittest.mock import ANY

TEST_OUTPUT_DIR = "test_output"
TEST_BACKUP_DIR = "test_output_backup"

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """ Setup and cleanup test directories before and after tests """
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)  # ✅ Always create test_output/
    os.makedirs(TEST_BACKUP_DIR, exist_ok=True)  # ✅ Always create test_output_backup/

    yield  # Run tests

    # ✅ Cleanup after tests
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    if os.path.exists(TEST_BACKUP_DIR):
        shutil.rmtree(TEST_BACKUP_DIR)

@patch("subprocess.run")
def test_run_script_success(mock_run):
    """ Test running a script without errors """
    mock_run.return_value.returncode = 0
    run_script("scripts/convert_to_absolute.py")
    mock_run.assert_called_with(["python3", "scripts/convert_to_absolute.py"], check=True, stdout=ANY, stderr=ANY)


@patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
def test_run_script_failure(mock_run):
    """ Test handling errors when running a script """
    with pytest.raises(subprocess.CalledProcessError):
        run_script("scripts/convert_to_absolute.py")

def test_prepare_output_folder():
    """ Test backup logic in prepare_output_folder """
    prepare_output_folder()
    assert os.path.exists(TEST_BACKUP_DIR)

@patch("subprocess.run")
def test_compile_book(mock_run):
    """ Test compiling book using Pandoc """
    compile_book("pdf")
    mock_run.assert_called()
