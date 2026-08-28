from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import *


class TerminalUI:
    def __init__(self, engine: EconomyEngine):
        self.engine = engine

    def parse_command(self, raw_input: str) -> tuple[str, int]:
        """Parses 'b 5' into ('b', 5). Handles errors internally."""
        parts = raw_input.split()
        if not parts:
            raise ValueError("Input must contain a command.")

        command = parts[0]
        amount = int(parts[1]) if len(parts) > 1 else 1
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return command, amount

    def render(self):
        """Visualizes the Engine state."""
        # Accessing data from the Engine to display it
        m = self.engine.food_market

        print("-" * 40)
        print(f"MARKET: {m.product.name.title()} @ {m.current_price:.2f} €")
        print("-" * 40)
        print(self.engine.player)  # Uses Inventory.__str__
        print("-" * 40)
        # Formatting the raw history data for the user
        last_3 = self.engine.history[-3:]
        print(f"History: {last_3}")
        print("-" * 40)
        print("COMMANDS: 'b 1' (buy), 's 5' (sell), 'q' (quit)")

    def run(self):
        while True:
            self.render()
            user_input = input(">> ").strip().lower()

            if user_input == "q":
                print("Exiting...")
                break

            try:
                cmd, amount = self.parse_command(user_input)

                if cmd == "b":
                    action, price = self.engine.interact_with_market(
                        is_buy=True, quantity=amount
                    )
                    print(f"\n[SUCCESS] {action} {amount} units @ {price:.2f}\n")
                elif cmd == "s":
                    action, price = self.engine.interact_with_market(
                        is_buy=False, quantity=amount
                    )
                    print(f"\n[SUCCESS] {action} {amount} units @ {price:.2f}\n")
                else:
                    print("\n[!] Unknown command.\n")

                # Advance the game world
                self.engine.tick()

            except ValueError as e:
                print(f"\n[!] Invalid input format: {e}\nExample: 'b 5' or 's 1'.\n")
            except GameException as e:
                # Catching the logic errors from the Engine
                print(f"\n[!] TRANSACTION FAILED: {e}\n")
