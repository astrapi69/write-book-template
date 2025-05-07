import pytest
import os
import shutil
from pathlib import Path
from scripts.convert_to_absolute import convert_to_absolute

TEST_MANUSCRIPT_DIR = "test_manuscript"
TEST_ASSETS_DIR = "test_assets"


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """ Setup test environment and clean up afterward """
    os.makedirs(TEST_MANUSCRIPT_DIR, exist_ok=True)
    os.makedirs(TEST_ASSETS_DIR, exist_ok=True)

    test_markdown = Path(TEST_MANUSCRIPT_DIR) / "test.md"
    test_image = Path(TEST_ASSETS_DIR) / "test-image.png"

    with open(test_markdown, "w") as f:
        f.write('![Test Image](../test_assets/test-image.png)')

    with open(test_image, "wb") as f:
        f.write(b"fake image data")

    yield  # Run tests

    shutil.rmtree(TEST_MANUSCRIPT_DIR)
    shutil.rmtree(TEST_ASSETS_DIR)


def test_convert_markdown_images_to_absolute():
    """ Test conversion of relative paths to absolute paths """
    convert_to_absolute([TEST_MANUSCRIPT_DIR])  # ✅ Pass the test directory as a list

    test_markdown = Path(TEST_MANUSCRIPT_DIR) / "test.md"
    with open(test_markdown, "r") as f:
        content = f.read()

    expected_path = str((Path(TEST_ASSETS_DIR) / "test-image.png").resolve())

    assert expected_path in content, f"❌ Expected {expected_path} but got {content}"
