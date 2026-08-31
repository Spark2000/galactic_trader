"""Product definitions and their immutable starting values."""

from dataclasses import dataclass
from enum import Enum

from galactic_trader.cargo import CargoType


@dataclass(frozen=True)
class ProductInfo:
    """Describres pre-definied product informations."""

    display_name: str
    starting_price: float
    starting_volatility: float
    cargo_type: CargoType
    distance: int

    def __post_init__(self) -> None:
        """Validates the initial starting values."""
        if not self.display_name.strip():
            raise ValueError("Displayname must not be empty.")
        if self.starting_volatility < 0:
            raise ValueError("Volatility must not be negative.")
        if self.starting_price < 1.0:
            raise ValueError("Price must be greater or equal to one.")
        if not isinstance(self.cargo_type, CargoType):
            raise TypeError("Cargo type must be an instance of CargoType.")
        if self.distance <= 0:
            raise ValueError("Distance must be greater than zero.")


class Product(Enum):
    """Enum that contains all procuts and declared their ProductInfo values"""

    # Basic resources
    FOOD = ProductInfo("Food", 10.0, 0.50, CargoType.REFRIGERATED, 35)
    WOOD = ProductInfo("Wood", 8.0, 0.45, CargoType.STANDARD, 45)
    ORE = ProductInfo("Ore", 6.0, 0.40, CargoType.STANDARD, 60)
    OIL = ProductInfo("Oil", 12.0, 0.85, CargoType.LIQUID, 75)
    GEMS = ProductInfo("Gems", 35.0, 1.75, CargoType.STANDARD, 110)

    # Processed materials
    METAL = ProductInfo("Metal", 16.0, 0.65, CargoType.STANDARD, 50)
    NAILS = ProductInfo("Nails", 20.0, 0.55, CargoType.STANDARD, 30)
    FUEL = ProductInfo("Fuel", 30.0, 1.20, CargoType.LIQUID, 65)
    CHEMICALS = ProductInfo("Chemicals", 38.0, 1.30, CargoType.HAZARDOUS, 85)
    TEXTILES = ProductInfo("Textiles", 31.0, 0.90, CargoType.STANDARD, 55)

    # Consumer and industrial goods
    FURNITURE = ProductInfo("Furniture", 52.0, 1.50, CargoType.STANDARD, 40)
    CLOTHING = ProductInfo("Clothing", 78.0, 2.00, CargoType.STANDARD, 45)
    MEDICINE = ProductInfo("Medicine", 68.0, 2.40, CargoType.REFRIGERATED, 80)
    MACHINES = ProductInfo("Machines", 86.0, 2.80, CargoType.STANDARD, 90)
    ELECTRONICS = ProductInfo("Electronics", 118.0, 3.50, CargoType.STANDARD, 105)
    JEWELRY = ProductInfo("Jewelry", 115.0, 4.00, CargoType.STANDARD, 100)

    # High-value goods
    WEAPONS = ProductInfo("Weapons", 240.0, 6.00, CargoType.HAZARDOUS, 130)
    ROBOTS = ProductInfo("Robots", 310.0, 7.50, CargoType.STANDARD, 145)
    STARSHIP_PARTS = ProductInfo(
        "Starship Parts", 415.0, 10.00, CargoType.STANDARD, 170
    )

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

    @property
    def cargo_type(self) -> CargoType:
        """Return the required cargo type."""
        product_info: ProductInfo = self.value
        return product_info.cargo_type

    @property
    def distance(self) -> int:
        """Return the one-way distance to the product's source."""
        return self.value.distance

    def __str__(self) -> str:
        """
        Returns a human-readable string of the product name.

        >>> str(Product.FOOD)
        'Food'
        """
        return self.value.display_name
