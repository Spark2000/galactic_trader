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
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        return {
            material: amount_per_unit * quantity
            for material, amount_per_unit in self.materials.items()
        }

    def calculate_total_cost(self, quantity: int) -> float:
        """Calculates the total costs for a given production quantity."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        return self.cost * quantity


# Mapping funktioniert aehnlich zu dict, verhindert aber das aendern der Werte (nur Lesezugriff!)
PRODUCTION_RECIPES: dict[Product, ProductionRecipe] = {
    # Tier 1: processing basic resources
    Product.METAL: ProductionRecipe(
        materials={Product.ORE: 2},
        cost=2.0,
    ),
    Product.NAILS: ProductionRecipe(
        materials={Product.METAL: 1},
        cost=1.0,
    ),
    Product.FUEL: ProductionRecipe(
        materials={Product.OIL: 2},
        cost=2.0,
    ),
    # Tier 2: consumer and industrial goods
    Product.FURNITURE: ProductionRecipe(
        materials={
            Product.WOOD: 2,
            Product.NAILS: 1,
        },
        cost=7.0,
    ),
    Product.CLOTHING: ProductionRecipe(
        materials={Product.TEXTILES: 2},
        cost=5.0,
    ),
    Product.MEDICINE: ProductionRecipe(
        materials={
            Product.CHEMICALS: 1,
            Product.FOOD: 1,
        },
        cost=8.0,
    ),
    Product.MACHINES: ProductionRecipe(
        materials={
            Product.METAL: 2,
            Product.FUEL: 1,
        },
        cost=10.0,
    ),
    Product.ELECTRONICS: ProductionRecipe(
        materials={
            Product.METAL: 1,
            Product.GEMS: 1,
            Product.CHEMICALS: 1,
        },
        cost=10.0,
    ),
    Product.JEWELRY: ProductionRecipe(
        materials={
            Product.GEMS: 2,
            Product.METAL: 1,
        },
        cost=10.0,
    ),
    # Tier 3: advanced goods
    Product.WEAPONS: ProductionRecipe(
        materials={
            Product.METAL: 2,
            Product.CHEMICALS: 1,
            Product.ELECTRONICS: 1,
        },
        cost=15.0,
    ),
    Product.ROBOTS: ProductionRecipe(
        materials={
            Product.MACHINES: 1,
            Product.ELECTRONICS: 1,
            Product.FUEL: 1,
        },
        cost=25.0,
    ),
    Product.STARSHIP_PARTS: ProductionRecipe(
        materials={
            Product.MACHINES: 2,
            Product.ELECTRONICS: 1,
            Product.METAL: 1,
        },
        cost=40.0,
    ),
}
