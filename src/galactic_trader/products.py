from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ProductInfo:
    display_name: str
    starting_price: float
    starting_volatility: float

    def __post_init__(self) -> None:
        """Validates the initial starting values."""
        if self.starting_volatility < 0:
            raise ValueError("Volatility must not be negative.")
        if self.starting_price < 1.0:
            raise ValueError("Price must be greater or equal to one.")


class Product(Enum):
    FOOD = ProductInfo(
        display_name="Food", starting_price=10.0, starting_volatility=0.5
    )
    FURNITURE = ProductInfo(
        display_name="Furniture", starting_price=50.0, starting_volatility=0.3
    )
    NAILS = ProductInfo(
        display_name="Nails", starting_price=1.5, starting_volatility=0.1
    )
    WOOD = ProductInfo(
        display_name="Wood", starting_price=13.0, starting_volatility=0.8
    )
    # TODO more products e.g. ore, metal, ...

    @property
    def display_name(self) -> str:
        """Return the display name."""
        return self.value.display_name

    @property
    def starting_price(self) -> float:
        """Return the starting market price."""
        return self.value.starting_price

    @property
    def starting_volatility(self) -> float:
        """Return the starting market volatility."""
        return self.value.starting_volatility

    def __str__(self) -> str:
        """
        Returns a human-readable string of the product name.

        >>> str(Product.FOOD)
        'Food'
        """
        return self.value.display_name
