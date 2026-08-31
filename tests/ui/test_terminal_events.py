"""Tests for event output in the terminal interface."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product
from galactic_trader.ships import ShipModel
from galactic_trader.transport import TransportMission
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


"""BELOW ARE TESTS REGARDING TRANSPORT EVENTS (PIRAT ATTACK)"""


def test_next_round_displays_defended_pirate_attack(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The terminal reports a pirate attack and its successful defense."""
    engine = EconomyEngine(
        random_seed=1,
        event_probability=0,
        pirate_attack_probability=1,
    )
    ship = engine.fleet.add_ship(
        ShipModel(
            model_id="terminal_pirate_test",
            display_name="Terminal Test Ship",
            cargo_type=CargoType.STANDARD,
            cargo_capacity=10,
            speed_rating=50,
            defense_rating=100,
            purchase_price=1.0,
        )
    )
    ship.start_transport(
        TransportMission(
            product=Product.GEMS,
            quantity=2,
            total_rounds=2,
            remaining_rounds=2,
        )
    )
    terminal = TerminalUI(engine)
    commands = iter(["n", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr(terminal, "render", lambda: None)

    terminal.run()

    output = capsys.readouterr().out
    assert "[PIRATES]" in output
    assert "Terminal Test Ship (ID: #1) repelled a pirate attack" in output
    assert "No cargo was lost" in output
