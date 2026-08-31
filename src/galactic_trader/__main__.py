"""Command-line entry point for Galactic Trader."""

from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Sequence
from math import isfinite

from galactic_trader.engine import EconomyEngine


def parse_money(value: str) -> float:
    """Parse and validate the requested starting money."""
    try:
        money = float(value)
    except ValueError:
        raise ArgumentTypeError("Money must be a number.") from None

    if not isfinite(money) or money < 0:
        raise ArgumentTypeError(
            "Money must be a finite, non-negative number."
        )

    return round(money, 2)


def build_parser() -> ArgumentParser:
    """Build the command-line parser used to configure the game."""
    parser = ArgumentParser(description="Start Galactic Trader.")

    parser.add_argument(
        "--ui",
        choices=("pygame", "terminal"),
        default="pygame",
        help="Choose the graphical or terminal interface (default: pygame).",
    )

    parser.add_argument(
        "--money",
        type=parse_money,
        default=100.0,
        metavar="CREDITS",
        help="Set the player's starting Credits (default: 100).",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Start Galactic Trader with the selected configuration."""
    arguments = build_parser().parse_args(argv)

    logic = EconomyEngine(starting_money=arguments.money)

    if arguments.ui == "terminal":
        from galactic_trader.ui.terminal import TerminalUI

        TerminalUI(logic).run()
    else:
        from galactic_trader.ui.pygame_ui import PygameUI

        PygameUI(logic).run()


if __name__ == "__main__":
    main()