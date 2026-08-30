"""Stores and updates player money and stock."""

from dataclasses import dataclass, field

from galactic_trader.exceptions import NotEnoughMoneyException, NotEnoughStockException
from galactic_trader.production import ProductionRecipe
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
        assert quantity != 0
        assert unit_price > 0

        cost = quantity * unit_price

        # 1. Validation Logic
        if quantity > 0:  # BUYING
            if self.money < cost:
                raise NotEnoughMoneyException(
                    f"Need {cost:.2f} Credits, have {self.money:.2f} Credits"
                )

        elif quantity < 0:  # SELLING
            # check current stock. absolute value needed because quantity is negative
            current_stock = self.stock.get(product, 0)
            if current_stock < abs(quantity):
                raise NotEnoughStockException(f"Not enough {product} to sell.")

        # 2. Execution Logic (Only runs if Validation passes)
        self.money -= cost
        self.adjust_stock(product, quantity)

    def execute_production(
        self, product: Product, quantity: int, recipe: ProductionRecipe
    ) -> float:
        """
        Executes the production of given product.
        Removes the required materials and production cost and adds the produced products at given quantity
        """
        assert quantity > 0

        total_cost = recipe.calculate_total_cost(quantity)
        required_materials = recipe.calculate_required_materials(quantity)

        if self.money < total_cost:
            raise NotEnoughMoneyException(
                f"Need {total_cost:.2f} Credits, have {self.money:.2f} Credits"
            )

        missing_materials = {
            material: required_amount - self.stock.get(material, 0)
            for material, required_amount in required_materials.items()
            if self.stock.get(material, 0) < required_amount
        }

        if missing_materials:
            missing_display = ", ".join(
                f"{amount} {material}" for material, amount in missing_materials.items()
            )
            raise NotEnoughStockException(f"Missing materials: {missing_display}.")

        # only change inventory values after checks have passed
        self.money -= total_cost

        for material, required_amount in required_materials.items():
            self.stock[material] -= required_amount

        self.adjust_stock(product, quantity)

        return total_cost

    def adjust_stock(self, product: Product, change: int) -> None:
        """Adjusts (increases/ decreses) amount by given value."""
        current_amount = self.stock.get(product, 0)

        if change < 0 and current_amount < abs(change):
            raise ValueError("Stock value cannot be negative, change value ist too low")

        self.stock[product] = current_amount + change

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
