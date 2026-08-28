from dataclasses import dataclass

from galactic_trader.products import ProductType


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
