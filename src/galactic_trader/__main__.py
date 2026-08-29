from galactic_trader.engine import EconomyEngine
from galactic_trader.ui.terminal import TerminalUI


def main() -> None:
    """Start Galactic Trader with the terminal interface."""
    logic = EconomyEngine()
    app = TerminalUI(logic)
    app.run()


if __name__ == "__main__":
    main()
