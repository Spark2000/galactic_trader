"""Stores and updates player money and stock."""

from dataclasses import dataclass, field

from galactic_trader.exceptions import (
    NotEnoughMaterialsException,
    NotEnoughMoneyException,
    NotEnoughStockException,
)
from galactic_trader.production import ProductionRecipe
from galactic_trader.products import Product


@dataclass
class Inventory:
    """Manages the player's credits and products currently in the stock."""

    money: float
    stock: dict[Product, int] = field(default_factory=dict)

    def pay(self, amount: float) -> None:
        """Deducts a positive amount after checking the available credits."""
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        if self.money < amount:
            raise NotEnoughMoneyException(
                f"Need {amount:.2f} Credits, have {self.money:.2f} Credits."
            )
        self.money = round(self.money - amount, 2)

    def credit(self, amount: float) -> None:
        """Adds a positive amount to the player's credits."""
        if amount <= 0:
            raise ValueError("Credit amount must be greater than zero.")
        self.money = round(self.money + amount, 2)

    def execute_sale(
        self,
        product: Product,
        quantity: int,
        unit_price: float,
    ) -> None:
        """Executes an immediate stock sale."""
        if quantity <= 0:
            raise ValueError("Sale quantity must be greater than zero.")
        if unit_price <= 0:
            raise ValueError("Unit price must be greater than zero.")

        current_stock = self.stock.get(product, 0)
        if current_stock < quantity:
            raise NotEnoughStockException(f"Not enough {product} to sell.")

        total = round(quantity * unit_price, 2)
        self.adjust_stock(product, -quantity)
        self.credit(total)

    def execute_production(
        self, product: Product, quantity: int, recipe: ProductionRecipe
    ) -> float:
        """Consumes materials and credits and adds the produced products."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

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
            raise NotEnoughMaterialsException(f"Missing materials: {missing_display}.")

        # only change inventory values after checks have passed
        self.pay(total_cost)
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
