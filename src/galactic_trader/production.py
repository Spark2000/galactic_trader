"""Immutable production recipes and the games recipe registry."""

from dataclasses import dataclass

from galactic_trader.products import Product


@dataclass(frozen=True)
class ProductionRecipe:
    """
    Requirements for producing a specific product

    materials : dictonary with required products (key) and amount (value) for production
    cost : production costs
    """

    materials: dict[Product, int]
    cost: float

    def __post_init__(self) -> None:
        """Validate the recipe."""
        if not self.materials:
            raise ValueError("A recipe requires at least one material.")

        if any(amount <= 0 for amount in self.materials.values()):
            raise ValueError("Material amounts must be greater than zero.")

        if self.cost <= 0:
            raise ValueError("Production cost must be greater than zero.")

    def calculate_required_materials(self, quantity: int) -> dict[Product, int]:
        """Calculates the materials required for a given production quantity."""
        assert quantity > 0

        return {
            material: amount_per_unit * quantity
            for material, amount_per_unit in self.materials.items()
        }

    def calculate_total_cost(self, quantity: int) -> float:
        """Calculates the total costs for a given production quantity."""
        assert quantity > 0

        return self.cost * quantity


# Mapping funktioniert aehnlich zu dict, verhindert aber das aendern der Werte (nur Lesezugriff!)
PRODUCTION_RECIPES: dict[Product, ProductionRecipe] = {
    Product.FURNITURE: ProductionRecipe(
        {
            Product.WOOD: 2,
            Product.NAILS: 4,
        },
        5.0,
    ),
    Product.NAILS: ProductionRecipe(
        {
            Product.METAL: 1,
        },
        1.0,
    ),
}
