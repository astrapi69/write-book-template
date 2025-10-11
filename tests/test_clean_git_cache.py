# tests/test_clean_git_cache.py
from pathlib import Path
import subprocess
import pytest

from scripts.clean_git_cache import clean_git_cache


class DummyCompleted:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr


def test_clean_git_cache_calls_commands_in_order(monkeypatch, tmp_path: Path, capsys):
    calls = []

    def fake_run(cmd, cwd=None, check=True, capture_output=True, text=True):
        # record the call
        calls.append((tuple(cmd), Path(cwd) if cwd else None))
        # mimic successful git output
        return DummyCompleted(stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Act
    clean_git_cache(cwd=tmp_path, aggressive=True, prune="now")

    # Assert order & args
    assert len(calls) == 2
    assert calls[0][0] == ("git", "reflog", "expire", "--expire=now", "--all")
    assert calls[0][1] == tmp_path

    assert calls[1][0] == ("git", "gc", "--prune=now", "--aggressive")
    assert calls[1][1] == tmp_path

    # Ensure user-friendly prints happened
    out = capsys.readouterr().out
    assert "🧹 Cleaning Git object cache safely..." in out
    assert "✅ Git object cache cleaned successfully." in out


def test_clean_git_cache_propagates_errors(monkeypatch, tmp_path: Path):
    def fake_run_fail(cmd, cwd=None, check=True, capture_output=True, text=True):
        raise subprocess.CalledProcessError(
            returncode=128,
            cmd=cmd,
            stderr="fatal: not a git repository (or any of the parent directories): .git",
        )

    monkeypatch.setattr(subprocess, "run", fake_run_fail)

    with pytest.raises(subprocess.CalledProcessError) as exc:
        clean_git_cache(cwd=tmp_path)

    assert exc.value.returncode == 128
    assert "not a git repository" in (exc.value.stderr or "").lower()


def test_clean_git_cache_non_aggressive(monkeypatch, tmp_path: Path):
    recorded = {}

    def fake_run(cmd, cwd=None, check=True, capture_output=True, text=True):
        # store last command per 'phase'
        if cmd[1] == "reflog":
            recorded["reflog"] = cmd
        elif cmd[1] == "gc":
            recorded["gc"] = cmd
        return DummyCompleted()

    monkeypatch.setattr(subprocess, "run", fake_run)

    clean_git_cache(cwd=tmp_path, aggressive=False, prune="1.week.ago")

    assert recorded["reflog"] == [
        "git",
        "reflog",
        "expire",
        "--expire=1.week.ago",
        "--all",
    ]
    assert recorded["gc"] == ["git", "gc", "--prune=1.week.ago"]  # no --aggressive
