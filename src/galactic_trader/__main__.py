from galactic_trader.engine import EconomyEngine
from galactic_trader.ui.terminal import TerminalUI

if __name__ == "__main__":
    logic = EconomyEngine()
    app = TerminalUI(logic)
    app.run()
