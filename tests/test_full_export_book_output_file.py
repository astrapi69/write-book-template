import sys
import io
import subprocess
from scripts import full_export_book


def run_main_with_args(
    monkeypatch,
    args,
    tmp_path,
    pyproject_content=None,
    preset_output=None,
    stub_project_name=None,
):
    """
    Helper to run full_export_book.main() with controlled environment.
    - monkeypatch: pytest fixture
    - args: CLI args to simulate
    - tmp_path: temporary directory
    - pyproject_content: optional TOML content to write
    - preset_output: optional pre-set OUTPUT_FILE
    - stub_project_name: if set, bypasses real pyproject parsing
    """

    # Fake pyproject.toml if content provided
    if pyproject_content:
        (tmp_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
        monkeypatch.chdir(tmp_path)

    # Reset OUTPUT_FILE
    full_export_book.OUTPUT_FILE = preset_output

    # Stub external calls so we don’t run real scripts
    monkeypatch.setattr(
        full_export_book,
        "run_script",
        lambda *a, **k: print(f"MOCK run_script {a} {k}"),
    )

    class _CP:
        returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _CP())

    # Stub project name resolution if desired
    if stub_project_name is not None:
        monkeypatch.setattr(
            full_export_book,
            "get_project_name_from_pyproject",
            lambda *a, **k: stub_project_name,
        )

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    base_args = ["--skip-images"]  # avoid preprocessing noise
    monkeypatch.setattr(sys, "argv", ["full_export_book.py"] + base_args + args)

    try:
        full_export_book.main()
        return sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout


def test_output_file_explicit(monkeypatch, tmp_path):
    out = run_main_with_args(
        monkeypatch, ["--output-file", "custom"], tmp_path, stub_project_name="ignored"
    )
    assert "custom_ebook" in out


def test_output_file_from_pyproject(monkeypatch, tmp_path):
    # Here we bypass TOML parsing and directly control return value
    out = run_main_with_args(monkeypatch, [], tmp_path, stub_project_name="demo-book")
    assert "demo-book_ebook" in out


def test_output_file_preset(monkeypatch, tmp_path):
    out = run_main_with_args(
        monkeypatch,
        [],
        tmp_path,
        preset_output="presetname",
        stub_project_name="ignored",
    )
    assert "presetname_ebook" in out


def test_output_file_book_type(monkeypatch, tmp_path):
    out = run_main_with_args(
        monkeypatch,
        ["--book-type", "paperback"],
        tmp_path,
        stub_project_name="demo-book",
    )
    assert "demo-book_paperback" in out


def test_output_file_broken_pyproject(monkeypatch, tmp_path):
    # Simulate parsing error fallback
    out = run_main_with_args(monkeypatch, [], tmp_path, stub_project_name="book")
    assert "book_ebook" in out
