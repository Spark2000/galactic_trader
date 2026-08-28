import sys
import os
from dataclasses import dataclass, field
from itertools import cycle
from enum import Enum, auto
from typing import Optional


class GameException(Exception):
    """Base class for all game-related errors."""
    pass

class NotEnoughMoneyException(GameException):
    pass

class NotEnoughStockException(GameException):
    pass

class ProductType(Enum):
    FOOD = auto()
    # Später auch andere Produkte

    def __str__(self):
        return self.name.title()


@dataclass
class Inventory:
    """Each player has one inventory"""

    money: float
    stock: dict[ProductType, int] = field(default_factory=dict)

    def execute_trade(self, product: ProductType, quantity: int, unit_price: float):
        """
        Unified method for Buying AND Selling.
        - Positive quantity = BUY (Money down, Stock up)
        - Negative quantity = SELL (Money up, Stock down)
        """
        cost = quantity * unit_price

        # 1. Validation Logic
        if quantity > 0:  # BUYING
            if self.money < cost:
                raise NotEnoughMoneyException(
                    f"Need {cost:.2f}€, have {self.money:.2f}€"
                )

        elif quantity < 0:  # SELLING
            # check current stock. absolute value needed because quantity is negative
            current_stock = self.stock.get(product, 0)
            if current_stock < abs(quantity):
                raise NotEnoughStockException(f"Not enough {product.name} to sell.")

        # 2. Execution Logic (Only runs if Validation passes)
        self.money -= cost
        current_qty = self.stock.get(product, 0)
        self.stock[product] = current_qty + quantity

    def __str__(self) -> str:
        """Creates a pretty, human-readable string for the player."""
        money_display = f"{self.money:.2f} €"
        items_list = [
            f"{product.name.title()}: {amount}"
            for product, amount in self.stock.items()
            if amount > 0
        ]
        stock_display = ", ".join(items_list) if items_list else "Empty"
        return f"[Money: {money_display} | Stock: {stock_display}]"


@dataclass
class Market:
    """For each product type, there is one market"""

    product: ProductType
    current_price: float
    volatility: float

    def adjust_price(self, direction: int) -> None:
        """
        Adjusts price based on supply/demand.
        direction: 1 for Buy (Demand up), -1 for Sell (Supply up).
        """
        change = direction * self.volatility
        new_price = self.current_price + change
        self.current_price = max(1.0, round(new_price, 2))



class EconomyEngine:
    def __init__(self):
        # 1. Initialize State
        self.player = Inventory(money=100.0)
        self.food_market = Market(
            product=ProductType.FOOD, current_price=10.0, volatility=0.5
        )
        self.history: list[tuple] = []
        self.market_trend = cycle([0.2, 0.2, -0.1, -0.3])

    def interact_with_market(self, is_buy: bool, quantity: int) -> tuple[str, float]:
        """
        Executes the trade logic.
        Returns details of the transaction (Action Name, Total Price)
        or raises an exception.
        """
        market = self.food_market
        # Math: Buy is positive quantity, Sell is negative
        signed_qty = quantity if is_buy else -quantity

        # 1. Execute logic (Raises exceptions if invalid)
        self.player.execute_trade(market.product, signed_qty, market.current_price)

        # 2. Update History
        action_name = "BUY" if is_buy else "SELL"
        self.history.append((action_name, quantity, market.current_price))

        # 3. Update Market Price (Supply/Demand)
        # +1 direction for Buy, -1 for Sell
        direction = 1 if is_buy else -1
        market.adjust_price(direction)

        return action_name, market.current_price

    def tick(self):
        """Advances the simulation by one step (Background market forces)."""
        trend = next(self.market_trend)
        new_price = self.food_market.current_price + trend
        self.food_market.current_price = max(1.0, round(new_price, 2))



class TerminalUI:
    def __init__(self, engine: EconomyEngine):
        self.engine = engine

    def parse_command(self, raw_input: str) -> tuple[str, int]:
        """Parses 'b 5' into ('b', 5). Handles errors internally."""
        parts = raw_input.split()
        if not parts:
            raise ValueError("Empty command")

        command = parts[0]
        amount = int(parts[1]) if len(parts) > 1 else 1
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

            except ValueError:
                print("\n[!] Invalid input format. Use 'b 5' or 's 1'.\n")
            except GameException as e:
                # Catching the logic errors from the Engine
                print(f"\n[!] TRANSACTION FAILED: {e}\n")



if __name__ == "__main__":
    # In a Jupyter notebook, this blocks the cell until 'q' is pressed.
    logic = EconomyEngine()
    app = TerminalUI(logic)
    app.run()