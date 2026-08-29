import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product
from galactic_trader.ui.terminal import TerminalUI


@pytest.fixture
def terminal_ui() -> TerminalUI:
    return TerminalUI(EconomyEngine())


def test_parse_command_buy(terminal_ui: TerminalUI) -> None:
    result = terminal_ui.parse_command("b food 5")

    assert result == ("b", Product.FOOD, 5)


def test_parse_command_sell(terminal_ui: TerminalUI) -> None:
    result = terminal_ui.parse_command("s wood")

    assert result == ("s", Product.WOOD, 1)


def test_parse_command_next(terminal_ui: TerminalUI) -> None:
    result = terminal_ui.parse_command("n")

    assert result == ("n", None, 0)


def test_parse_command_quit(terminal_ui: TerminalUI) -> None:
    result = terminal_ui.parse_command("q")

    assert result == ("q", None, 0)


def test_parse_command_buy_with_default_amount(terminal_ui: TerminalUI) -> None:
    result = terminal_ui.parse_command("b food")

    assert result == ("b", Product.FOOD, 1)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "b",
        "x food 5",
        "b unknown 5",
        "b food zero",
        "b food 0",
        "b food -1",
        "b food 5 additional",
        "n food",
        "n 1",
        "quit",
    ],
)
def test_parse_command_rejects_invalid_input(
    terminal_ui: TerminalUI, invalid_input: str
) -> None:
    with pytest.raises(ValueError):
        terminal_ui.parse_command(invalid_input)
