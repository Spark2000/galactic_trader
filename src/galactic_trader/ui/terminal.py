"""Terminal-based user interface for Galactic Trader."""

from dataclasses import dataclass

from galactic_trader.cargo import CargoType
from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import GameException
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_models
from galactic_trader.transport import TransportOption


@dataclass(frozen=True)
class ParsedCommand:
    """Represent one validated terminal command."""

    action: str
    product: Product | None = None
    amount: int = 0
    ship_model_id: str | None = None
    ship_id: int | None = None


class TerminalUI:
    """Parses terminal commands and renders the current game state."""

    def __init__(self, engine: EconomyEngine) -> None:
        """Initializes the terminal interface."""
        self.engine = engine

    def parse_command(self, raw_input: str) -> ParsedCommand:
        """Parse and validate one terminal command."""
        parts = raw_input.split()
        if not parts:
            raise ValueError("Input cannot be empty.")

        command = parts[0].lower()

        if command == "help":
            if len(parts) == 2 and parts[1].lower() == "ships":
                return ParsedCommand(action="help_ships")
            raise ValueError("Expected 'help ships'.")

        if command == "my":
            if len(parts) == 2 and parts[1].lower() == "ships":
                return ParsedCommand(action="my_ships")
            raise ValueError("Expected 'my ships'.")

        if command == "buy" and len(parts) >= 2 and parts[1].lower() == "ship":
            if len(parts) != 3:
                raise ValueError("Expected 'buy ship <model_id>'.")
            return ParsedCommand(action="buy_ship", ship_model_id=parts[2].lower())

        if command == "sell" and len(parts) >= 2 and parts[1].lower() == "ship":
            if len(parts) != 3:
                raise ValueError("Expected 'sell ship <ship_id>'.")
            try:
                ship_id = int(parts[2])
            except ValueError:
                raise ValueError("Ship ID must be a whole number.") from None
            if ship_id <= 0:
                raise ValueError("Ship ID must be greater than zero.")
            return ParsedCommand(action="sell_ship", ship_id=ship_id)

        if command in {"n", "q"}:
            if len(parts) != 1:
                raise ValueError(f"Command '{command}' takes no arguments.")
            return ParsedCommand(action=command)

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

        return ParsedCommand(action=command, product=product, amount=amount)

    def select_transport_ship(self, options: tuple[TransportOption, ...]) -> int | None:
        """Displays transport options and ask for a ship ID or cancellation."""
        if not options:
            return None

        print("\nAVAILABLE SPACESHIPS:")
        available_ids = {option.ship_id for option in options}
        for option in options:
            round_label = "round" if option.travel_rounds == 1 else "rounds"
            print(
                f"- #{option.ship_id}: {option.ship_name} "
                f"| Capacity: {option.cargo_capacity} "
                f"| Expected travel time: "
                f"{option.travel_rounds} {round_label}"
            )

        while True:
            selection = input("Ship ID or 'c' to cancel: ").strip().lower()
            if selection == "c":
                return None
            try:
                ship_id = int(selection)
            except ValueError:
                print("[!] Ship ID must be a whole number or 'c'.")
                continue
            if ship_id not in available_ids:
                print("[!] Select one of the displayed spaceship IDs.")
                continue
            return ship_id

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
            "- Products:\n"
            "  - buy: 'b <product> <amount>'\n"
            "  - sell: 's <product> <amount>'\n"
            "  - produce: 'p <product> <amount>'\n"
            "- Spaceship:\n"
            "  - buy: 'buy ship <model_id>'\n"
            "  - sell: 'sell ship <ship_id>'\n"
            "  - owned spaceships: 'my ships'\n"
            "  - spaceship catalog: 'help ships'\n"
            "- Other:\n"
            "  - next round: 'n'\n"
            "  - quit: 'q'"
        )

    def render_products(self) -> None:
        """Displays all available products."""
        print("MARKET:")

        for m in self.engine.markets.values():
            print(
                f"- {m.product} @ {m.current_price:.2f} Credits ({m.product.cargo_type})"
            )

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

    def render_ship_models(self) -> None:
        """Display all spaceship models grouped by supported cargo type."""
        print("SPACESHIP MODELS:")

        for cargo_type in CargoType:
            print(f"\n{cargo_type}:")

            for model in get_ship_models(cargo_type):
                print(
                    f"- [{model.model_id}] {model.display_name} "
                    f"| Capacity: {model.cargo_capacity} "
                    f"| Speed: {model.speed_rating} "
                    f"| Defense: {model.defense_rating} "
                    f"| Price: {model.purchase_price:.2f} Credits"
                )

    def render_owned_ships(self) -> None:
        """Display every spaceship currently owned by the player."""
        print("YOUR SPACESHIPS:")
        if not self.engine.fleet.ships:
            print("- No spaceships owned.")
            return

        for owned_ship in self.engine.fleet.ships:
            model = owned_ship.model
            if owned_ship.active_transport is None:
                status = "Available"
            else:
                mission = owned_ship.active_transport
                status = (
                    f"In transit: {mission.quantity} {mission.product}, "
                    f"{mission.remaining_rounds}/{mission.total_rounds} "
                    "rounds remaining"
                )
            print(
                f"- {owned_ship} "
                f"| Cargo: {model.cargo_type} "
                f"| Capacity: {model.cargo_capacity} "
                f"| Speed: {model.speed_rating} "
                f"| Defense: {model.defense_rating}"
                f"| Status: {status}"
            )

    def run(self) -> None:
        """Run the terminal input loop until the user quits."""
        while True:
            self.render()
            user_input = input(">> ").strip().lower()

            try:
                cmd = self.parse_command(user_input)

                if cmd.action == "q":
                    print("Exiting...")
                    break
                if cmd.action == "n":
                    result = self.engine.tick()
                    print("\n[NEXT] Next Round started.")
                    if result.market_event is None:
                        print("[EVENT] No market event this round.")
                    else:
                        print(f"[EVENT] {result.market_event.message}")
                    for delivery in result.completed_deliveries:
                        print(f"[DELIVERY] {delivery.message}")
                    continue
                if cmd.action == "help_ships":
                    self.render_ship_models()
                    continue
                if cmd.action == "my_ships":
                    self.render_owned_ships()
                    continue
                if cmd.action == "buy_ship":
                    assert cmd.ship_model_id is not None
                    owned_ship, price = self.engine.buy_ship(cmd.ship_model_id)
                    print(f"\n[SUCCESS] Bought {owned_ship} for {price:.2f} Credits.\n")
                    continue
                if cmd.action == "sell_ship":
                    assert cmd.ship_id is not None
                    owned_ship, price = self.engine.sell_ship(cmd.ship_id)
                    print(f"\n[SUCCESS] Sold {owned_ship} for {price:.2f} Credits.\n")
                    continue

                assert cmd.product is not None

                if cmd.action == "b":
                    options = self.engine.get_transport_options(
                        cmd.product,
                        cmd.amount,
                    )
                    if not options:
                        print(
                            f"\n[!] No available spaceship can transport "
                            f"{cmd.amount} {cmd.product}. "
                            "Purchase cancelled.\n"
                        )
                        continue

                    ship_id = self.select_transport_ship(options)
                    if ship_id is None:
                        print("\n[!] Purchase cancelled.\n")
                        continue

                    purchase = self.engine.buy_product(
                        cmd.product,
                        cmd.amount,
                        ship_id,
                    )
                    print(
                        f"\n[SUCCESS] Bought {purchase.quantity} "
                        f"{purchase.product} @ "
                        f"{purchase.unit_price:.2f} Credits.\n"
                        f"[TRANSPORT] {purchase.ship_name} "
                        f"(ID: #{purchase.ship_id}) returns in "
                        f"{purchase.travel_rounds} round(s).\n"
                    )
                elif cmd.action == "s":
                    action, price = self.engine.interact_with_market(
                        is_buy=False, product=cmd.product, quantity=cmd.amount
                    )
                    print(f"\n[SUCCESS] {action} {cmd.amount} units @ {price:.2f}\n")
                elif cmd.action == "p":
                    action, price = self.engine.produce_product(
                        product=cmd.product, quantity=cmd.amount
                    )
                    print(f"\n[SUCCESS] {action} {cmd.amount} units @ {price:.2f}\n")

            except ValueError as e:
                print(f"\n[!] Invalid input format: {e}")
            except GameException as e:
                print(f"\n[!] TRANSACTION FAILED: {e}\n")
