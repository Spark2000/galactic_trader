"""Terminal-based user interface for Galactic Trader."""

from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import GameException
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product


class TerminalUI:
    """Parses terminal commands and renders the current game state."""

    def __init__(self, engine: EconomyEngine) -> None:
        """Initializes the terminal interface."""
        self.engine = engine

    def parse_command(self, raw_input: str) -> tuple[str, Product | None, int]:
        """Parses '<command> <product> <amount>' into its components. Handles errors internally."""
        parts = raw_input.split()

        if not parts:
            raise ValueError("Input cannot be empty.")

        command = parts[0].lower()
        if command in {"n", "q"}:
            if len(parts) != 1:
                raise ValueError(f"Command '{command}' takes no arguments.")
            return command, None, 0

        if command not in {"b", "s", "p"}:
            raise ValueError(f"Command '{command}' is unknown.")
        if len(parts) not in {2, 3}:
            raise ValueError(
                "Expected '<command> <product> <amount>', e.g. ‘b food 3‘."
            )

        product_name = parts[1].upper()
        try:
            product = Product[product_name]
        except KeyError:
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
        self.render_products()
        print("-" * 40)
        self.render_production_recipes()
        print("-" * 40)
        print(self.engine.player)  # Uses Inventory.__str__
        print("-" * 40)

        # Formatting the raw history data for the user
        last_3 = self.engine.history[-3:]
        print(f"History: {last_3}")

        print("-" * 40)
        print(
            "COMMANDS:\n"
            "- buy: 'b <product> <amount>',\n"
            "- sell: 's <product> <amount>'\n"
            "- next round: 'n'"
            "- quit: 'q'"
        )

    def render_products(self) -> None:
        """Displays all available products."""
        print("MARKET:")

        for m in self.engine.markets.values():
            print(f"- {m.product} @ {m.current_price:.2f} Credits")

    def render_production_recipes(self) -> None:
        """Displays all available production recipes."""
        print("PRODUCTION RECIPES:")

        for product, recipe in PRODUCTION_RECIPES.items():
            materials_display = ", ".join(
                f"{amount} {material}" for material, amount in recipe.materials.items()
            )
            print(
                f"- {product}: {recipe.cost:.2f} Credits | Materials: {materials_display}"
            )

    def run(self) -> None:
        """Game loop for terminal ui."""
        while True:
            self.render()
            user_input = input(">> ").strip().lower()

            try:
                cmd, product, amount = self.parse_command(user_input)

                if cmd == "q":
                    print("Exiting...")
                    break
                if cmd == "n":
                    event = self.engine.tick()
                    print("\n[NEXT] Next Round started.")
                    if event is None:
                        print("[EVENT] No market event this round.")
                    else:
                        print(f"[EVENT] {event.message}")
                    continue

                assert product is not None

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
                elif cmd == "p":
                    action, price = self.engine.produce_product(
                        product=product, quantity=amount
                    )
                    print(f"\n[SUCCESS] {action} {amount} units @ {price:.2f}\n")

            except ValueError as e:
                print(f"\n[!] Invalid input format: {e}")
            except GameException as e:
                # Catching the logic errors from the Engine
                print(f"\n[!] TRANSACTION FAILED: {e}\n")
