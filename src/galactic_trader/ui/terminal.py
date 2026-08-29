from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import GameException
from galactic_trader.products import Product


class TerminalUI:
    def __init__(self, engine: EconomyEngine) -> None:
        """Initializes the terminal interface."""
        self.engine = engine

    def parse_command(self, raw_input: str) -> tuple[str, Product, int]:
        """Parses '<command> <product> <amount>' into its components. Handles errors internally."""
        parts = raw_input.split()
        if len(parts) not in {2, 3}:
            raise ValueError("Expected '<command> <product> <amount>', e.g. ‘b food 3‘.")

        command = parts[0].lower()

        product_name = parts[1].upper()
        try:
            product = Product[product_name]
        except(KeyError):
            available_products = ", ".join(product.name.lower() for product in Product)
            raise ValueError(
                f"Input must contain an available product. Given product '{parts[1]}' is unknown.\n"
                f"Available products: {available_products}."
            ) from None

        try:
            amount = int(parts[2]) if len(parts) == 3 else 1
        except ValueError:
            raise ValueError("Amount must be a whole number.")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        
        return command, product, amount

    def render(self) -> None:
        """Visualizes the Engine state."""
        print("-" * 40)
        print("MARKET:")

        for m in self.engine.markets.values():
            print(f"- {m.product} @ {m.current_price:.2f} Credits")

        print("-" * 40)
        print(self.engine.player)  # Uses Inventory.__str__
        print("-" * 40)

        # Formatting the raw history data for the user
        last_3 = self.engine.history[-3:]
        print(f"History: {last_3}")

        print("-" * 40)
        print(
            "COMMANDS: 'b <product> <amount>' (buy), 's <product> <amount>' (sell), 'q' (quit)"
        )

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
                print(
                    f"\n[!] Invalid input format: {e}\nExample: 'b food 5' or 's food 1'.\n"
                )
            except GameException as e:
                # Catching the logic errors from the Engine
                print(f"\n[!] TRANSACTION FAILED: {e}\n")
