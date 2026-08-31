"""Product definitions and their immutable starting values."""

from dataclasses import dataclass
from enum import Enum

from galactic_trader.cargo import CargoType
from galactic_trader.planets import Planet


@dataclass(frozen=True)
class ProductInfo:
    """Describres pre-definied product informations."""

    display_name: str
    starting_price: float
    starting_volatility: float
    cargo_type: CargoType
    planet: Planet

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
        if not isinstance(self.planet, Planet):
            raise TypeError("Planet must be an instance of Planet.")


class Product(Enum):
    """Enum that contains all procuts and declared their ProductInfo values"""

    # Basic resources
    FOOD = ProductInfo("Food", 10.0, 0.50, CargoType.REFRIGERATED, Planet.ALDERAAN)
    WOOD = ProductInfo("Wood", 8.0, 0.45, CargoType.STANDARD, Planet.ENDOR)
    ORE = ProductInfo("Ore", 6.0, 0.40, CargoType.STANDARD, Planet.KESSEL)
    OIL = ProductInfo("Oil", 12.0, 0.85, CargoType.LIQUID, Planet.ABAFAR)
    GEMS = ProductInfo("Gems", 35.0, 1.75, CargoType.STANDARD, Planet.KESSEL)

    # Processed materials
    METAL = ProductInfo("Metal", 16.0, 0.65, CargoType.STANDARD, Planet.KESSEL)
    NAILS = ProductInfo("Nails", 20.0, 0.55, CargoType.STANDARD, Planet.KESSEL)
    FUEL = ProductInfo("Fuel", 30.0, 1.20, CargoType.LIQUID, Planet.ABAFAR)
    CHEMICALS = ProductInfo("Chemicals", 38.0, 1.30, CargoType.HAZARDOUS, Planet.KAMINO)
    TEXTILES = ProductInfo("Textiles", 31.0, 0.90, CargoType.STANDARD, Planet.CORUSCANT)

    # Consumer and industrial goods
    FURNITURE = ProductInfo(
        "Furniture", 52.0, 1.50, CargoType.STANDARD, Planet.CORUSCANT
    )
    CLOTHING = ProductInfo("Clothing", 78.0, 2.00, CargoType.STANDARD, Planet.CORUSCANT)
    MEDICINE = ProductInfo(
        "Medicine", 68.0, 2.40, CargoType.REFRIGERATED, Planet.KAMINO
    )
    MACHINES = ProductInfo("Machines", 86.0, 2.80, CargoType.STANDARD, Planet.KUAT)
    ELECTRONICS = ProductInfo(
        "Electronics", 118.0, 3.50, CargoType.STANDARD, Planet.KUAT
    )
    JEWELRY = ProductInfo("Jewelry", 115.0, 4.00, CargoType.STANDARD, Planet.CORUSCANT)

    # High-value goods
    WEAPONS = ProductInfo("Weapons", 240.0, 6.00, CargoType.HAZARDOUS, Planet.GEONOSIS)
    ROBOTS = ProductInfo("Robots", 310.0, 7.50, CargoType.STANDARD, Planet.GEONOSIS)
    STARSHIP_PARTS = ProductInfo(
        "Starship Parts", 415.0, 10.00, CargoType.STANDARD, Planet.KUAT
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
        return self.value.cargo_type

    @property
    def planet(self) -> Planet:
        """Return the planet from which the product is collected."""
        return self.value.planet

    @property
    def distance(self) -> int:
        """Return the distance to the product's planet."""
        return self.planet.distance

    def __str__(self) -> str:
        """
        Returns a human-readable string of the product name.

        >>> str(Product.FOOD)
        'Food'
        """
        return self.value.display_name
