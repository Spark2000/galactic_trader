from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from galactic_trader.products import Product


@dataclass(frozen=True)
class CraftingRecipe:
    """
    Requirements for producing a specific product

    materials : dictonary with required products (key) and amount (value) for production
    cost : production costs
    """

    materials: Mapping[Product, int]
    cost: float

    def __post_init__(self) -> None:
        """Validate the recipe."""
        if not self.materials:
            raise ValueError("A recipe requires at least one material.")

        if any(amount <= 0 for amount in self.materials.values()):
            raise ValueError("Material amounts must be greater than zero.")

        if self.cost <= 0:
            raise ValueError("Production cost must be greater than zero.")


# Mapping funktioniert aehnlich zu dict, verhindert aber das aendern der Werte (nur Lesezugriff!)
CRAFTING_RECIPES: Mapping[Product, CraftingRecipe] = MappingProxyType(
    {
        Product.FURNITURE: CraftingRecipe(
            {
                Product.WOOD: 2,
                Product.NAILS: 4,
            },
            5.0,
        ),
        Product.NAILS: CraftingRecipe(
            {
                Product.METAL: 1,
            },
            1.0
        )
    }
)
