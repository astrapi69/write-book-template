# tests/test_print_version_build_print_pipeline.py
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

import scripts.print_version_build as bp


class DummyProc:
    def __init__(self, returncode: int = 0):
        self.returncode = returncode


def make_dummy_scripts(scripts_dir: Path) -> None:
    """
    Create the minimal scripts the pipeline expects.
    We only *need* full_export_book.py now, but we also create a couple no-ops
    for backwards compatibility with earlier helper behavior.
    """
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Minimal noop full_export_book.py (must exist; logic is monkeypatched)
    (scripts_dir / "full_export_book.py").write_text(
        dedent(
            """\
            #!/usr/bin/env python3
            if __name__ == "__main__":
                pass
            """
        ),
        encoding="utf-8",
    )

    # Optional extras (not actually invoked by current pipeline)
    (scripts_dir / "convert_links_to_plain_text.py").write_text(
        "pass\n", encoding="utf-8"
    )
    (scripts_dir / "strip_links.py").write_text("pass\n", encoding="utf-8")


def _is_python_invocation(cmd: list[str]) -> bool:
    """Heuristic: first arg is path/name containing 'python'."""
    if not cmd:
        return False
    head = cmd[0]
    return (
        head.endswith("python")
        or head.endswith("python3")
        or head.endswith("python.exe")
        or "python" in head
    )


def test_pipeline_order_and_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts_dir = tmp_path / "scripts"
    make_dummy_scripts(scripts_dir)

    calls: list[list[str]] = []

    def fake_run(cmd, check=True):
        calls.append(cmd)
        return DummyProc(0)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    # Expect git restore to run at end
    argv = ["--scripts-dir", str(scripts_dir)]
    with pytest.raises(SystemExit) as ex:
        bp.main(argv)
    assert ex.value.code == 0

    # Verify order: one python invocation (full_export_book) and a git restore at the end
    py = [c for c in calls if _is_python_invocation(c)]
    assert len(py) == 1, f"Expected exactly one python call, got {len(py)}: {calls}"
    assert py[0][1].endswith(
        "full_export_book.py"
    ), f"Expected full_export_book.py, got: {py[0]}"

    git = [c for c in calls if c and c[0] == "git"]
    assert git, "Expected a git call to restore working tree"
    assert git[-1][1:] == [
        "restore",
        ".",
    ], f"Expected final git call to be 'restore .', got: {git[-1]}"

    out, _ = capsys.readouterr()
    assert "Print version EPUB successfully generated" in out


def test_pipeline_aborts_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scripts_dir = tmp_path / "scripts"
    make_dummy_scripts(scripts_dir)

    def fake_run(cmd, check=True):
        # Fail on the only pipeline step now: full_export_book.py
        if len(cmd) > 1 and cmd[1].endswith("full_export_book.py"):
            raise bp.subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return DummyProc(0)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    argv = ["--scripts-dir", str(scripts_dir), "--no-restore"]
    with pytest.raises(SystemExit) as ex:
        bp.main(argv)

    assert ex.value.code == 1, "Pipeline should abort with exit code 1 on step failure"

    out, _ = capsys.readouterr()
    assert "Build process aborted." in out
