"""Tests for spaceship help in the terminal interface."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.engine import EconomyEngine
from galactic_trader.ships import get_all_ship_models
from galactic_trader.ui.terminal import TerminalUI


@pytest.fixture
def terminal() -> TerminalUI:
    """Create a deterministic terminal interface for testing."""
    engine = EconomyEngine(random_seed=15, event_probability=0)
    return TerminalUI(engine)


def test_parse_command_help_ships(terminal: TerminalUI) -> None:
    result = terminal.parse_command("help ships")

    assert result == ("help_ships", None, 0)


@pytest.mark.parametrize(
    "invalid_command",
    [
        "help",
        "help products",
        "help ships additional",
    ],
)
def test_parse_command_rejects_unknown_help_topic(
    terminal: TerminalUI,
    invalid_command: str,
) -> None:
    with pytest.raises(ValueError):
        terminal.parse_command(invalid_command)


def test_render_ship_models_displays_every_registered_model(
    terminal: TerminalUI,
    capsys: pytest.CaptureFixture[str],
) -> None:
    terminal.render_ship_models()

    output = capsys.readouterr().out
    assert "SPACESHIP MODELS:" in output

    for cargo_type in CargoType:
        assert f"{cargo_type}:" in output

    for model in get_all_ship_models():
        assert model.display_name in output
        assert f"Capacity: {model.cargo_capacity}" in output
        assert f"Speed: {model.speed_rating}" in output
        assert f"Defense: {model.defense_rating}" in output
        assert f"Price: {model.purchase_price:.2f} Credits" in output


def test_run_executes_help_ships_command(
    terminal: TerminalUI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter(["help ships", "q"])

    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "SPACESHIP MODELS:" in output
    assert "Titan Carrier" in output
    assert "Exiting..." in output
