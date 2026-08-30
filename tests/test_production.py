"""Tests for production recipe validation and calculations."""

import pytest

from galactic_trader.production import PRODUCTION_RECIPES, ProductionRecipe
from galactic_trader.products import Product


def test_recipe_stores_materials_and_cost() -> None:
    materials = {
        Product.WOOD: 2,
        Product.NAILS: 4,
    }

    recipe = ProductionRecipe(materials=materials, cost=5.0)

    assert recipe.materials == materials
    assert recipe.cost == pytest.approx(5.0)


def test_recipe_rejects_empty_materials() -> None:
    with pytest.raises(ValueError):
        ProductionRecipe(materials={}, cost=5.0)


@pytest.mark.parametrize("invalid_amount", [0, -1])
def test_recipe_rejects_nonpositive_material_amounts(invalid_amount: int) -> None:
    with pytest.raises(ValueError):
        ProductionRecipe(
            materials={Product.WOOD: invalid_amount},
            cost=5.0,
        )


@pytest.mark.parametrize("invalid_cost", [0.0, -1.0])
def test_recipe_rejects_nonpositive_cost(invalid_cost: float) -> None:
    with pytest.raises(ValueError):
        ProductionRecipe(
            materials={Product.WOOD: 2},
            cost=invalid_cost,
        )


def test_calculate_required_materials_scales_every_material() -> None:
    recipe = ProductionRecipe(
        materials={
            Product.WOOD: 2,
            Product.NAILS: 4,
        },
        cost=5.0,
    )

    required_materials = recipe.calculate_required_materials(quantity=3)

    assert required_materials == {
        Product.WOOD: 6,
        Product.NAILS: 12,
    }


def test_calculate_required_materials_does_not_change_recipe() -> None:
    recipe = ProductionRecipe(
        materials={Product.WOOD: 2},
        cost=5.0,
    )

    required_materials = recipe.calculate_required_materials(quantity=3)
    required_materials[Product.WOOD] = 100

    assert recipe.materials == {Product.WOOD: 2}


def test_calculate_total_cost_scales_with_quantity() -> None:
    recipe = ProductionRecipe(
        materials={Product.WOOD: 2},
        cost=5.0,
    )

    total_cost = recipe.calculate_total_cost(quantity=3)

    assert total_cost == pytest.approx(15.0)


@pytest.mark.parametrize("quantity", [0, -1])
def test_calculations_require_positive_quantity(
    quantity: int,
) -> None:
    recipe = ProductionRecipe(
        materials={Product.WOOD: 2},
        cost=5.0,
    )

    with pytest.raises(ValueError):
        recipe.calculate_required_materials(quantity)

    with pytest.raises(ValueError):
        recipe.calculate_total_cost(quantity)
