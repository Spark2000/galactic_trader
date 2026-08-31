"""Tests for interactive transport selection and delivery output."""

import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model
from galactic_trader.transport import TransportOption
from galactic_trader.ui.terminal import TerminalUI


@pytest.fixture
def terminal() -> TerminalUI:
    """Create a deterministic terminal with one standard-cargo ship."""
    engine = EconomyEngine(random_seed=15, event_probability=0)
    engine.player.money = 1000.0
    engine.fleet.add_ship(get_ship_model("standard_s_1"))
    return TerminalUI(engine)


def test_ship_selection_displays_duration_and_returns_ship_id(
    terminal: TerminalUI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    options = (
        TransportOption(
            ship_id=3,
            ship_name="Comet Courier",
            cargo_capacity=10,
            travel_rounds=2,
        ),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "3")

    selected_id = terminal.select_transport_ship(options)

    output = capsys.readouterr().out
    assert selected_id == 3
    assert "#3: Comet Courier" in output
    assert "Expected travel time: 2 rounds" in output


def test_ship_selection_repeats_after_invalid_id(
    terminal: TerminalUI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter(["999", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    options = terminal.engine.get_transport_options(Product.WOOD, 1)

    selected_id = terminal.select_transport_ship(options)

    assert selected_id == 1
    assert "Select one of the displayed spaceship IDs" in capsys.readouterr().out


def test_buy_without_available_ship_is_cancelled_without_changes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    engine = EconomyEngine(random_seed=15, event_probability=0)
    terminal = TerminalUI(engine)
    starting_money = engine.player.money
    commands = iter(["b wood 1", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "No available spaceship can transport 1 Wood" in output
    assert engine.player.money == starting_money
    assert engine.history == []
    assert engine.player.stock.get(Product.WOOD, 0) == 0


def test_player_can_cancel_ship_selection_without_buying(
    terminal: TerminalUI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    starting_money = terminal.engine.player.money
    commands = iter(["b wood 2", "c", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "Purchase cancelled" in output
    assert terminal.engine.player.money == starting_money
    assert terminal.engine.history == []


def test_run_starts_transport_and_displays_delivery(
    terminal: TerminalUI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter(["b wood 2", "1", "my ships", "n", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "AVAILABLE SPACESHIPS:" in output
    assert "Expected travel time: 1 round" in output
    assert "Bought 2 Wood" in output
    assert "In transit: 2 Wood" in output
    assert "[DELIVERY] 2 Wood arrived with Comet Courier (ID: #1)" in output
    assert terminal.engine.player.stock[Product.WOOD] == 2
    assert terminal.engine.fleet.get_ship(1).is_available


def test_owned_ship_render_shows_available_status(
    terminal: TerminalUI,
    capsys: pytest.CaptureFixture[str],
) -> None:
    terminal.render_owned_ships()

    output = capsys.readouterr().out
    assert "Comet Courier (ID: #1)" in output
    assert "Status: Available" in output
