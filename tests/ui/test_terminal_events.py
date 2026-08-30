"""Tests for event output in the terminal interface."""

import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.ui.terminal import TerminalUI


def test_next_round_displays_triggered_event(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    terminal = TerminalUI(
        EconomyEngine(random_seed=15, event_probability=1),
    )
    commands = iter(["n", "q"])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "[NEXT] Next Round started." in output
    assert "[EVENT]" in output
    assert "No market event" not in output


def test_next_round_displays_when_no_event_occurs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    terminal = TerminalUI(
        EconomyEngine(random_seed=15, event_probability=0),
    )
    commands = iter(["n", "q"])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "[EVENT] No market event this round." in output
