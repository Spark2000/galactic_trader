"""Command-line entry point for Galactic Trader."""

from argparse import ArgumentParser
from collections.abc import Sequence

from galactic_trader.engine import EconomyEngine


def build_parser() -> ArgumentParser:
    """Build the command-line parser used to select a user interface."""
    parser = ArgumentParser(description="Start Galactic Trader.")
    parser.add_argument(
        "--ui",
        choices=("pygame", "terminal"),
        default="pygame",
        help="Choose the graphical or terminal interface (default: pygame).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Start Galactic Trader with the selected interface."""
    arguments = build_parser().parse_args(argv)
    logic = EconomyEngine()

    if arguments.ui == "terminal":
        from galactic_trader.ui.terminal import TerminalUI

        TerminalUI(logic).run()
    else:
        from galactic_trader.ui.pygame_ui import PygameUI

        PygameUI(logic).run()


if __name__ == "__main__":
    main()
