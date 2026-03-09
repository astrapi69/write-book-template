#!/usr/bin/env python3
# tests/test_make_tag_message_test_ask_helpers.py
"""Tests for interactive ask_* helpers in scripts/make_tag_message.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import module under test (lives in scripts/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import make_tag_message as mtm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def disable_questionary(monkeypatch):
    """Force fallback (no questionary) for all tests unless overridden."""
    monkeypatch.setattr(mtm, "questionary", None)


def make_questionary_mock():
    """Create a mock questionary module with chainable .ask() API."""
    mock = MagicMock()

    def _chain(return_value):
        chain = MagicMock()
        chain.ask.return_value = return_value
        return chain

    mock._chain = _chain
    return mock


# ===========================================================================
# ask_confirm
# ===========================================================================


class TestAskConfirmFallback:
    """Tests for ask_confirm without questionary (input() fallback)."""

    @pytest.mark.parametrize("user_input", ["y", "yes", "Y", "YES", "Yes"])
    def test_yes_variants(self, user_input):
        with patch("builtins.input", return_value=user_input):
            assert mtm.ask_confirm("Continue?") is True

    @pytest.mark.parametrize("user_input", ["j", "ja", "J", "JA", "Ja"])
    def test_german_yes_variants(self, user_input):
        with patch("builtins.input", return_value=user_input):
            assert mtm.ask_confirm("Weiter?") is True

    @pytest.mark.parametrize("user_input", ["n", "no", "N", "NO", "No"])
    def test_no_variants(self, user_input):
        with patch("builtins.input", return_value=user_input):
            assert mtm.ask_confirm("Continue?") is False

    @pytest.mark.parametrize("user_input", ["nein", "NEIN", "Nein"])
    def test_german_no_variants(self, user_input):
        with patch("builtins.input", return_value=user_input):
            assert mtm.ask_confirm("Weiter?") is False

    def test_empty_returns_default_false(self):
        with patch("builtins.input", return_value=""):
            assert mtm.ask_confirm("Continue?", default=False) is False

    def test_empty_returns_default_true(self):
        with patch("builtins.input", return_value=""):
            assert mtm.ask_confirm("Continue?", default=True) is True

    def test_invalid_then_valid(self):
        """Nonsense input loops, then accepts valid input."""
        with patch("builtins.input", side_effect=["x", "maybe", "y"]):
            assert mtm.ask_confirm("Continue?") is True

    def test_invalid_then_no(self):
        with patch("builtins.input", side_effect=["abc", "n"]):
            assert mtm.ask_confirm("Continue?") is False

    def test_true_and_false_strings(self):
        with patch("builtins.input", return_value="true"):
            assert mtm.ask_confirm("Continue?") is True
        with patch("builtins.input", return_value="false"):
            assert mtm.ask_confirm("Continue?") is False

    def test_numeric_1_and_0(self):
        with patch("builtins.input", return_value="1"):
            assert mtm.ask_confirm("Continue?") is True
        with patch("builtins.input", return_value="0"):
            assert mtm.ask_confirm("Continue?") is False


class TestAskConfirmQuestionary:
    """Tests for ask_confirm with questionary."""

    def test_questionary_true(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.confirm.return_value = mock_q._chain(True)
        monkeypatch.setattr(mtm, "questionary", mock_q)
        assert mtm.ask_confirm("Continue?") is True

    def test_questionary_false(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.confirm.return_value = mock_q._chain(False)
        monkeypatch.setattr(mtm, "questionary", mock_q)
        assert mtm.ask_confirm("Continue?") is False

    def test_questionary_none_aborts(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.confirm.return_value = mock_q._chain(None)
        monkeypatch.setattr(mtm, "questionary", mock_q)
        with pytest.raises(SystemExit, match="Aborted"):
            mtm.ask_confirm("Continue?")


# ===========================================================================
# ask_choice
# ===========================================================================

CHOICES = ["Alpha", "Beta", "Gamma"]


class TestAskChoiceFallback:
    """Tests for ask_choice without questionary."""

    def test_select_by_number(self):
        with patch("builtins.input", return_value="1"):
            assert mtm.ask_choice("Pick:", CHOICES) == "Alpha"

    def test_select_last_by_number(self):
        with patch("builtins.input", return_value="3"):
            assert mtm.ask_choice("Pick:", CHOICES) == "Gamma"

    def test_select_by_exact_text(self):
        with patch("builtins.input", return_value="Beta"):
            assert mtm.ask_choice("Pick:", CHOICES) == "Beta"

    def test_empty_returns_default(self):
        with patch("builtins.input", return_value=""):
            assert mtm.ask_choice("Pick:", CHOICES, default="Beta") == "Beta"

    def test_out_of_range_then_valid(self):
        with patch("builtins.input", side_effect=["0", "5", "99", "2"]):
            assert mtm.ask_choice("Pick:", CHOICES) == "Beta"

    def test_nonsense_then_valid(self):
        with patch("builtins.input", side_effect=["xyz", "2"]):
            assert mtm.ask_choice("Pick:", CHOICES) == "Beta"

    def test_empty_without_default_loops(self):
        """Empty input without default should loop, not return."""
        with patch("builtins.input", side_effect=["", "1"]):
            assert mtm.ask_choice("Pick:", CHOICES, default=None) == "Alpha"

    def test_negative_number_loops(self):
        with patch("builtins.input", side_effect=["-1", "1"]):
            assert mtm.ask_choice("Pick:", CHOICES) == "Alpha"


class TestAskChoiceQuestionary:
    """Tests for ask_choice with questionary."""

    def test_questionary_returns_value(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.select.return_value = mock_q._chain("Beta")
        monkeypatch.setattr(mtm, "questionary", mock_q)
        assert mtm.ask_choice("Pick:", CHOICES) == "Beta"

    def test_questionary_none_aborts(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.select.return_value = mock_q._chain(None)
        monkeypatch.setattr(mtm, "questionary", mock_q)
        with pytest.raises(SystemExit, match="Aborted"):
            mtm.ask_choice("Pick:", CHOICES)


# ===========================================================================
# ask_text
# ===========================================================================


class TestAskTextFallback:
    """Tests for ask_text without questionary."""

    def test_returns_user_input(self):
        with patch("builtins.input", return_value="hello"):
            assert mtm.ask_text("Name:") == "hello"

    def test_empty_returns_default(self):
        with patch("builtins.input", return_value=""):
            assert mtm.ask_text("Name:", default="world") == "world"

    def test_empty_no_default_returns_empty(self):
        with patch("builtins.input", return_value=""):
            assert mtm.ask_text("Name:") == ""

    def test_strips_whitespace(self):
        with patch("builtins.input", return_value="  trimmed  "):
            assert mtm.ask_text("Name:") == "trimmed"

    def test_validate_called(self):
        validator = MagicMock()
        with patch("builtins.input", return_value="ok"):
            mtm.ask_text("Name:", validate=validator)
        validator.assert_called_once_with("ok")

    def test_validate_raises_propagates(self):
        def bad_validator(val):
            raise SystemExit("Invalid tag")

        with patch("builtins.input", return_value="bad"):
            with pytest.raises(SystemExit, match="Invalid tag"):
                mtm.ask_text("Tag:", validate=bad_validator)


class TestAskTextQuestionary:
    """Tests for ask_text with questionary."""

    def test_questionary_returns_value(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.text.return_value = mock_q._chain("answer")
        monkeypatch.setattr(mtm, "questionary", mock_q)
        assert mtm.ask_text("Name:") == "answer"

    def test_questionary_none_aborts(self, monkeypatch):
        mock_q = make_questionary_mock()
        mock_q.text.return_value = mock_q._chain(None)
        monkeypatch.setattr(mtm, "questionary", mock_q)
        with pytest.raises(SystemExit, match="Aborted"):
            mtm.ask_text("Name:")


# ===========================================================================
# ask_int
# ===========================================================================


class TestAskInt:
    """Tests for ask_int (always uses ask_text internally)."""

    def test_valid_number(self):
        with patch("builtins.input", return_value="42"):
            assert mtm.ask_int("Count:", default=10) == 42

    def test_empty_returns_default(self):
        with patch("builtins.input", return_value=""):
            assert mtm.ask_int("Count:", default=100) == 100

    def test_non_numeric_then_valid(self):
        with patch("builtins.input", side_effect=["abc", "xyz", "50"]):
            assert mtm.ask_int("Count:", default=10) == 50

    def test_below_minimum_then_valid(self):
        with patch("builtins.input", side_effect=["0", "-5", "3"]):
            assert mtm.ask_int("Count:", default=10, minimum=1) == 3

    def test_minimum_exact(self):
        with patch("builtins.input", return_value="1"):
            assert mtm.ask_int("Count:", default=10, minimum=1) == 1

    def test_float_string_rejected(self):
        with patch("builtins.input", side_effect=["3.14", "3"]):
            assert mtm.ask_int("Count:", default=10) == 3

    def test_zero_accepted_when_minimum_zero(self):
        with patch("builtins.input", return_value="0"):
            assert mtm.ask_int("Count:", default=10, minimum=0) == 0
