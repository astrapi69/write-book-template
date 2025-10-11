# tests/test_full_export_book_pipeline.py
import importlib.util
import sys
from pathlib import Path
import pytest


def _copy_script(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _import_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None, f"spec_from_file_location({name}) returned None"
    assert spec.loader is not None, f"spec.loader is None for {name}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def temp_project(tmp_path: Path):
    """
    Create a self-contained project layout so full_export_book.py's os.chdir("..")
    places it at this temp project root (because we import it from temp/scripts).
    """
    project = tmp_path
    # Folders
    (project / "scripts").mkdir(parents=True)
    (project / "manuscript" / "chapters").mkdir(parents=True)
    (project / "manuscript" / "front-matter").mkdir(parents=True)
    (project / "manuscript" / "back-matter").mkdir(parents=True)
    (project / "assets" / "img").mkdir(parents=True)
    (project / "config").mkdir(parents=True)
    (project / "output").mkdir(parents=True)

    # Minimal files
    (project / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "write-book-template"\n', encoding="utf-8"
    )
    (project / "config" / "metadata.yaml").write_text(
        "title: T\nlanguage: de\n", encoding="utf-8"
    )
    (project / "manuscript" / "chapters" / "01.md").write_text(
        "# Ch1\n\n![c](assets_image.png)\n", encoding="utf-8"
    )
    (project / "assets" / "img" / "cover.png").write_text("png", encoding="utf-8")

    return project


@pytest.fixture()
def wired_module(temp_project: Path):
    """
    Copy the real repo scripts into the temp project, then import full_export_book from there.
    """
    repo_root = Path(__file__).resolve().parents[1]
    # Copy scripts
    _copy_script(
        repo_root / "scripts" / "full_export_book.py",
        temp_project / "scripts" / "full_export_book.py",
    )
    _copy_script(
        repo_root / "scripts" / "convert_to_absolute.py",
        temp_project / "scripts" / "convert_to_absolute.py",
    )
    _copy_script(
        repo_root / "scripts" / "convert_to_relative.py",
        temp_project / "scripts" / "convert_to_relative.py",
    )

    feb = _import_from_path(
        "full_export_book", temp_project / "scripts" / "full_export_book.py"
    )
    return feb


def test_pipeline_runs_convert_scripts_in_correct_order(
    wired_module, temp_project, monkeypatch, capsys
):
    """
    Verifies that main() calls:
      1) convert_to_absolute.py
      2) convert_img_tags.py --to-absolute
      3) compile step(s)
      4) convert_to_relative.py
      5) convert_img_tags.py --to-relative
    in that order when images are NOT skipped.
    """
    feb = wired_module

    # Replace IMG_SCRIPT path (may not exist in tests) and capture calls to run_script
    calls = []

    def fake_run_script(script_path, arg=None):
        calls.append((Path(script_path).name, arg))

    # We won't actually run pandoc; capture compile calls instead
    compile_calls = []

    def fake_compile_book(
        fmt, order, cover_path=None, force_epub2=False, lang="en", custom_ext=None
    ):
        compile_calls.append((fmt, tuple(order), lang, custom_ext))

    monkeypatch.setattr(feb, "run_script", fake_run_script)
    monkeypatch.setattr(feb, "compile_book", fake_compile_book)
    # Ensure IMG_SCRIPT resolves to something predictable for display in 'calls'
    monkeypatch.setattr(
        feb, "IMG_SCRIPT", str(temp_project / "scripts" / "convert_img_tags.py")
    )

    # Run with one format to keep it simple
    argv = [sys.argv[0], "--format", "markdown", "--extension", "md"]
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")
    monkeypatch.setattr(sys, "argv", argv)

    feb.main()

    # Expect compile called once
    assert compile_calls, "compile_book() was not called"
    # Check order of pre/post steps
    expected = [
        ("convert_to_absolute.py", None),
        ("convert_img_tags.py", "--to-absolute"),
        # ... (compile happens here) ...
        ("convert_to_relative.py", None),
        ("convert_img_tags.py", "--to-relative"),
    ]
    # Filter only convert_* and img tag calls
    filtered = [
        c
        for c in calls
        if c[0]
        in ("convert_to_absolute.py", "convert_to_relative.py", "convert_img_tags.py")
    ]
    assert (
        filtered == expected
    ), f"Call order mismatch.\nExpected: {expected}\nGot:      {filtered}"


def test_skip_images_flag_skips_pre_and_post(wired_module, temp_project, monkeypatch):
    feb = wired_module
    calls = []

    def fake_run_script(script_path, arg=None):
        calls.append((Path(script_path).name, arg))

    # avoid pandoc
    monkeypatch.setattr(feb, "run_script", fake_run_script)
    monkeypatch.setattr(feb, "compile_book", lambda *a, **k: None)

    argv = [sys.argv[0], "--format", "markdown", "--extension", "md", "--skip-images"]
    monkeypatch.setattr(sys, "argv", argv)

    feb.main()

    # Expect no convert calls at all
    assert not calls, "convert scripts should not run when --skip-images is set"


def test_language_resolution_cli_overrides_metadata(
    wired_module, temp_project, monkeypatch
):
    feb = wired_module
    seen = {}

    def capture_compile(
        fmt, order, cover_path=None, force_epub2=False, lang="en", custom_ext=None
    ):
        seen["lang"] = lang

    monkeypatch.setattr(feb, "compile_book", capture_compile)
    # Don’t run external scripts in this test
    monkeypatch.setattr(feb, "run_script", lambda *a, **k: None)

    argv = [sys.argv[0], "--format", "markdown", "--extension", "md", "--lang", "en"]
    monkeypatch.setattr(sys, "argv", argv)

    feb.main()
    assert seen.get("lang") == "en", "CLI --lang should override metadata.yaml language"


def test_language_resolution_uses_metadata_when_cli_missing(
    wired_module, temp_project, monkeypatch
):
    feb = wired_module
    seen = {}

    def capture_compile(
        fmt, order, cover_path=None, force_epub2=False, lang="en", custom_ext=None
    ):
        seen["lang"] = lang

    monkeypatch.setattr(feb, "compile_book", capture_compile)
    # Don’t run external scripts in this test
    monkeypatch.setattr(feb, "run_script", lambda *a, **k: None)

    argv = [sys.argv[0], "--format", "markdown", "--extension", "md"]
    monkeypatch.setattr(sys, "argv", argv)

    feb.main()
    assert (
        seen.get("lang") == "de"
    ), "Should use language from metadata.yaml when CLI --lang not provided"


def test_run_script_bubbles_up_subprocess_errors(
    wired_module, temp_project, monkeypatch
):
    feb = wired_module

    class Boom(Exception):
        pass

    def fake_run(*args, **kwargs):
        # Mimic subprocess.CalledProcessError in a minimal way
        import subprocess

        raise subprocess.CalledProcessError(returncode=1, cmd="python3 script.py")

    # Patch subprocess.run used inside full_export_book.run_script
    import subprocess as _sub

    monkeypatch.setattr(_sub, "run", fake_run)

    with pytest.raises(Exception):
        feb.run_script(str(temp_project / "scripts" / "whatever.py"))
