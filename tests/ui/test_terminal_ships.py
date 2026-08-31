"""Tests for spaceship help in the terminal interface."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.engine import EconomyEngine
from galactic_trader.ships import get_all_ship_models
from galactic_trader.ui.terminal import ParsedCommand, TerminalUI


@pytest.fixture
def terminal() -> TerminalUI:
    """Create a deterministic terminal interface for testing."""
    engine = EconomyEngine(random_seed=15, event_probability=0)
    engine.player.money = 5000.0
    return TerminalUI(engine)


@pytest.mark.parametrize(
    ("raw_input", "expected"),
    [
        (
            "buy ship atlas_runner",
            ParsedCommand(
                action="buy_ship",
                ship_model_id="atlas_runner",
            ),
        ),
        (
            "sell ship 3",
            ParsedCommand(action="sell_ship", ship_id=3),
        ),
        (
            "my ships",
            ParsedCommand(action="my_ships"),
        ),
        (
            "help ships",
            ParsedCommand(action="help_ships"),
        ),
    ],
)
def test_parse_ship_commands(
    terminal: TerminalUI,
    raw_input: str,
    expected: ParsedCommand,
) -> None:
    assert terminal.parse_command(raw_input) == expected


@pytest.mark.parametrize(
    "invalid_input",
    [
        "buy ship",
        "buy ship atlas_runner 2",
        "sell ship",
        "sell ship zero",
        "sell ship 0",
        "my ship",
    ],
)
def test_parse_ship_commands_reject_invalid_input(
    terminal: TerminalUI,
    invalid_input: str,
) -> None:
    with pytest.raises(ValueError):
        terminal.parse_command(invalid_input)


def test_owned_ships_display_empty_fleet(
    terminal: TerminalUI,
    capsys: pytest.CaptureFixture[str],
) -> None:
    terminal.render_owned_ships()

    output = capsys.readouterr().out
    assert "YOUR SPACESHIPS:" in output
    assert "No spaceships owned." in output


def test_owned_ships_display_duplicate_models_separately(
    terminal: TerminalUI,
    capsys: pytest.CaptureFixture[str],
) -> None:
    terminal.engine.buy_ship("atlas_runner")
    terminal.engine.buy_ship("atlas_runner")

    terminal.render_owned_ships()

    output = capsys.readouterr().out
    assert "Atlas Runner (ID: #1)" in output
    assert "Atlas Runner (ID: #2)" in output


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
        assert model.model_id in output
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


def test_run_buys_displays_and_sells_ship(
    terminal: TerminalUI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter(
        [
            "buy ship atlas_runner",
            "my ships",
            "sell ship 1",
            "q",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "Bought Atlas Runner (ID: #1)" in output
    assert "Atlas Runner (ID: #1)" in output
    assert "Sold Atlas Runner (ID: #1)" in output
    assert terminal.engine.fleet.ships == ()
