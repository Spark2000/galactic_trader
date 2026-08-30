"""Product definitions and their immutable starting values."""

from dataclasses import dataclass
from enum import Enum


class CargoType(Enum):
    """Describes the type of cargo hold required for a product."""

    STANDARD = "Standard cargo"
    LIQUID = "Liquid cargo"
    REFRIGERATED = "Refrigerated cargo"
    HAZARDOUS = "Hazardous cargo"

    def __str__(self) -> str:
        """Return the player-friendly cargo type name."""
        return self.value


@dataclass(frozen=True)
class ProductInfo:
    """Describres pre-definied product informations."""

    display_name: str
    starting_price: float
    starting_volatility: float
    cargo_type: CargoType

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


class Product(Enum):
    """Enum that contains all procuts and declared their ProductInfo values"""

    # Basic resources
    FOOD = ProductInfo("Food", 10.0, 0.50, CargoType.REFRIGERATED)
    WOOD = ProductInfo("Wood", 8.0, 0.45, CargoType.STANDARD)
    ORE = ProductInfo("Ore", 6.0, 0.40, CargoType.STANDARD)
    OIL = ProductInfo("Oil", 12.0, 0.85, CargoType.LIQUID)
    GEMS = ProductInfo("Gems", 35.0, 1.75, CargoType.STANDARD)

    # Processed materials
    METAL = ProductInfo("Metal", 16.0, 0.65, CargoType.STANDARD)
    NAILS = ProductInfo("Nails", 20.0, 0.55, CargoType.STANDARD)
    FUEL = ProductInfo("Fuel", 30.0, 1.20, CargoType.LIQUID)
    CHEMICALS = ProductInfo("Chemicals", 38.0, 1.30, CargoType.HAZARDOUS)
    TEXTILES = ProductInfo("Textiles", 31.0, 0.90, CargoType.STANDARD)

    # Consumer and industrial goods
    FURNITURE = ProductInfo("Furniture", 52.0, 1.50, CargoType.STANDARD)
    CLOTHING = ProductInfo("Clothing", 78.0, 2.00, CargoType.STANDARD)
    MEDICINE = ProductInfo("Medicine", 68.0, 2.40, CargoType.REFRIGERATED)
    MACHINES = ProductInfo("Machines", 86.0, 2.80, CargoType.STANDARD)
    ELECTRONICS = ProductInfo("Electronics", 118.0, 3.50, CargoType.STANDARD)
    JEWELRY = ProductInfo("Jewelry", 115.0, 4.00, CargoType.STANDARD)

    # High-value goods
    WEAPONS = ProductInfo("Weapons", 240.0, 6.00, CargoType.HAZARDOUS)
    ROBOTS = ProductInfo("Robots", 310.0, 7.50, CargoType.STANDARD)
    STARSHIP_PARTS = ProductInfo("Starship Parts", 415.0, 10.00, CargoType.STANDARD)

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

    def __str__(self) -> str:
        """
        Returns a human-readable string of the product name.

        >>> str(Product.FOOD)
        'Food'
        """
        return self.value.display_name
