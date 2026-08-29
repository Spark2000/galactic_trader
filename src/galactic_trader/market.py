from dataclasses import dataclass

from galactic_trader.products import Product


@dataclass
class Market:
    """
    Represents a market for one product.

    product : associated Product
    current_price : current price to buy 1 of the product
    volatility : sets the price fluctations on buying/ selling of the product
    """

    product: Product
    current_price: float
    volatility: float

    def __post_init__(self) -> None:
        """Validates the initial market values."""
        if self.volatility < 0:
            raise ValueError("Volatility must not be negative.")
        if self.current_price < 1:
            raise ValueError("Current price must be greater or equal to one.")

    def adjust_price(self, direction: int) -> None:
        """
        Adjusts price based on supply/demand.
        direction:
            pos. for Buy (demand up -> price up),
            neg. for Sell (supply up -> price down).
        """
        change = direction * self.volatility
        self.set_price(self.current_price + change)

    def adjust_volatility(self, change: float) -> None:
        """Adds change value to the current volatility."""
        self.set_volatility(self.volatility + change)

    def set_price(self, new_price: float) -> None:
        """Sets current_price to a new value or 1.0 if 1.0 > new value."""
        self.current_price = max(1.0, round(new_price, 2))

    def set_volatility(self, new_volatility: float) -> None:
        """Sets volatility to a new value or 0 if new value is negative."""
        self.volatility = max(0.0, round(new_volatility, 2))
