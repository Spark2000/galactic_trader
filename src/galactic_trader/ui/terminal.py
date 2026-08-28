from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import *
from galactic_trader.products import Product


class TerminalUI:
    def __init__(self, engine: EconomyEngine):
        self.engine = engine

    def parse_command(self, raw_input: str) -> tuple[str, int]:
        """Parses 'b food 5' into ('b', 'foord', 5). Handles errors internally."""
        parts = raw_input.split()
        if not parts:
            raise ValueError("Input cannot be empty.")

        command = parts[0]
        prod = parts[1].upper() if len(parts) > 1 else "N/A"
        if prod.upper() in Product.__members__:
            product = Product[prod]
        else:
            raise ValueError("Input must contain an available product.")
        amount = int(parts[2]) if len(parts) > 2 else 1
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return command, product, amount

    def render(self):
        """Visualizes the Engine state."""
        # Accessing data from the Engine to display it
        m = self.engine.food_market

        print("-" * 40)
        print("MARTKET:")
        for m in self.engine.markets_by_product.values():
            print(f"- {m.product} @ {m.current_price:.2f} Credits")
        print("-" * 40)
        print(self.engine.player)  # Uses Inventory.__str__
        print("-" * 40)
        # Formatting the raw history data for the user
        last_3 = self.engine.history[-3:]
        print(f"History: {last_3}")
        print("-" * 40)
        print("COMMANDS: 'b <product> <amount>' (buy), 's <product> <amount>' (sell), 'q' (quit)")

    def run(self):
        while True:
            self.render()
            user_input = input(">> ").strip().lower()

            if user_input == "q":
                print("Exiting...")
                break

            try:
                cmd, product, amount = self.parse_command(user_input)

                if cmd == "b":
                    action, price = self.engine.interact_with_market(
                        is_buy=True, product=product, quantity=amount
                    )
                    print(f"\n[SUCCESS] {action} {amount} units @ {price:.2f}\n")
                elif cmd == "s":
                    action, price = self.engine.interact_with_market(
                        is_buy=False, product=product, quantity=amount
                    )
                    print(f"\n[SUCCESS] {action} {amount} units @ {price:.2f}\n")
                else:
                    print("\n[!] Unknown command.\n")

                # Advance the game world
                self.engine.tick()

            except ValueError as e:
                print(f"\n[!] Invalid input format: {e}\nExample: 'b food 5' or 's food 1'.\n")
            except GameException as e:
                # Catching the logic errors from the Engine
                print(f"\n[!] TRANSACTION FAILED: {e}\n")
