from dataclasses import dataclass, field

from galactic_trader.exceptions import NotEnoughMoneyException, NotEnoughStockException
from galactic_trader.products import Product


@dataclass
class Inventory:
    """Each player has one inventory"""

    money: float
    stock: dict[Product, int] = field(default_factory=dict)

    def execute_trade(self, product: Product, quantity: int, unit_price: float) -> None:
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
                raise NotEnoughStockException(f"Not enough {product} to sell.")

        # 2. Execution Logic (Only runs if Validation passes)
        self.money -= cost
        current_qty = self.stock.get(product, 0)
        self.stock[product] = current_qty + quantity

    def __str__(self) -> str:
        """Return a formatted, human-readable string of the player inventory."""
        money_display = f"{self.money:.2f} Credits"
        items_list = [
            f"{product}: {amount}"
            for product, amount in self.stock.items()
            if amount > 0
        ]
        stock_display = ", ".join(items_list) if items_list else "Empty"
        return f"[Money: {money_display} | Stock: {stock_display}]"
