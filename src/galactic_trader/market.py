from dataclasses import dataclass

from galactic_trader.products import ProductType


@dataclass
class Market:
    """
    Represents a market for one product.

    product : associated ProductType
    current_price : current price to buy 1 of the product
    volatility : sets the price fluctations on buying/ selling of the product
    """

    product: ProductType
    current_price: float
    volatility: float

    def __post_init__(self) -> None:
        """Validates the initial market values."""
        if self.volatility < 0:
            raise ValueError("Volatility must be positive.")
        if self.current_price < 1:
            raise ValueError("Current price must be greater or equal to one.")

    def adjust_price(self, direction: int) -> None:
        """
        Adjusts price based on supply/demand.
        direction:
            1 for Buy (demand up -> price up),
            -1 for Sell (supply up -> price down).
        """
        change = direction * self.volatility
        new_price = self.current_price + change
        self.current_price = max(1.0, round(new_price, 2))
