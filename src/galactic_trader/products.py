"""Product definitions and their immutable starting values."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ProductInfo:
    """
    Every Product has pre-definied informations.

    display_name : product name shown to user
    starting_price : product price at the beginning of the game
    starting_volatility : prdouct volatility at the beginning of the game
    """

    display_name: str
    starting_price: float
    starting_volatility: float

    def __post_init__(self) -> None:
        """Validates the initial starting values."""
        if not self.display_name.strip():
            raise ValueError("Displayname must not be empty.")
        if self.starting_volatility < 0:
            raise ValueError("Volatility must not be negative.")
        if self.starting_price < 1.0:
            raise ValueError("Price must be greater or equal to one.")


class Product(Enum):
    """Enum that contains all procuts and declared their ProductInfo values"""

    # Basic resources
    FOOD = ProductInfo("Food", 10.0, 0.50)
    WOOD = ProductInfo("Wood", 8.0, 0.45)
    ORE = ProductInfo("Ore", 6.0, 0.40)
    OIL = ProductInfo("Oil", 12.0, 0.85)
    GEMS = ProductInfo("Gems", 35.0, 1.75)

    # Processed materials
    METAL = ProductInfo("Metal", 16.0, 0.65)
    NAILS = ProductInfo("Nails", 20.0, 0.55)
    FUEL = ProductInfo("Fuel", 30.0, 1.20)
    CHEMICALS = ProductInfo("Chemicals", 38.0, 1.30)
    TEXTILES = ProductInfo("Textiles", 31.0, 0.90)

    # Consumer and industrial goods
    FURNITURE = ProductInfo("Furniture", 52.0, 1.50)
    CLOTHING = ProductInfo("Clothing", 78.0, 2.00)
    MEDICINE = ProductInfo("Medicine", 68.0, 2.40)
    MACHINES = ProductInfo("Machines", 86.0, 2.80)
    ELECTRONICS = ProductInfo("Electronics", 118.0, 3.50)
    JEWELRY = ProductInfo("Jewelry", 115.0, 4.00)

    # High-value goods
    WEAPONS = ProductInfo("Weapons", 240.0, 6.00)
    ROBOTS = ProductInfo("Robots", 310.0, 7.50)
    STARSHIP_PARTS = ProductInfo("Starship Parts", 415.0, 10.00)

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
