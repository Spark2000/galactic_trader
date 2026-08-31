"""Tests for trading, production and stock manipulation."""

import pytest

from galactic_trader.exceptions import (
    NotEnoughMaterialsException,
    NotEnoughMoneyException,
    NotEnoughStockException,
)
from galactic_trader.inventory import Inventory
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product


def test_payment_updates_money() -> None:
    inventory = Inventory(money=100.0)

    inventory.pay(25.0)

    assert inventory.money == pytest.approx(75.0)


def test_credit_updates_money() -> None:
    inventory = Inventory(money=100.0)

    inventory.credit(10.0)

    assert inventory.money == pytest.approx(110.0)


def test_payment_without_enough_money_is_rejected() -> None:
    inventory = Inventory(money=5.0)

    with pytest.raises(NotEnoughMoneyException):
        inventory.pay(10.0)

    assert inventory.money == 5.0


def test_sale_increases_money_and_reduces_stock() -> None:
    inventory = Inventory(money=100.0, stock={Product.WOOD: 3})

    inventory.execute_sale(Product.WOOD, quantity=2, unit_price=8.0)

    assert inventory.money == pytest.approx(100.0 + (2 * Product.WOOD.starting_price))
    assert inventory.stock[Product.WOOD] == 1


def test_sale_without_stock_is_rejected() -> None:
    inventory = Inventory(money=100.0)

    with pytest.raises(NotEnoughStockException):
        inventory.execute_sale(Product.WOOD, quantity=1, unit_price=8.0)

    assert inventory.money == 100.0
    assert inventory.stock == {}


@pytest.mark.parametrize(
    ("quantity", "unit_price"),
    [
        (0, 10.0),
        (1, 0.0),
        (1, -1.0),
    ],
)
def test_sell_rejects_invalid_values(quantity: int, unit_price: float) -> None:
    inventory = Inventory(money=100.0)

    with pytest.raises(ValueError):
        inventory.execute_sale(Product.FOOD, quantity, unit_price)


def test_production_consumes_scaled_resources() -> None:
    inventory = Inventory(money=100.0)
    product = Product.FURNITURE
    quantity = 2
    recipe = PRODUCTION_RECIPES[product]
    for material, amount_per_unit in recipe.materials.items():
        inventory.stock[material] = amount_per_unit * quantity

    total_cost = inventory.execute_production(product, quantity, recipe)

    assert total_cost == pytest.approx(recipe.cost * quantity)
    assert inventory.money == pytest.approx(100.0 - total_cost)
    assert inventory.stock[product] == quantity
    for material in recipe.materials:
        assert inventory.stock[material] == 0


def test_production_without_money_is_atomic() -> None:
    inventory = Inventory(money=0.0)
    product = Product.FURNITURE
    recipe = PRODUCTION_RECIPES[product]
    for material, amount_per_unit in recipe.materials.items():
        inventory.stock[material] = amount_per_unit
    stock_before = inventory.stock.copy()

    with pytest.raises(NotEnoughMoneyException):
        inventory.execute_production(product, 1, recipe)

    assert inventory.money == 0.0
    assert inventory.stock == stock_before


def test_production_without_materials_is_atomic() -> None:
    inventory = Inventory(money=100.0)
    product = Product.FURNITURE
    recipe = PRODUCTION_RECIPES[product]
    first_material = next(iter(recipe.materials))
    inventory.stock[first_material] = recipe.materials[first_material] - 1
    stock_before = inventory.stock.copy()

    with pytest.raises(NotEnoughMaterialsException):
        inventory.execute_production(product, 1, recipe)

    assert inventory.money == 100.0
    assert inventory.stock == stock_before


def test_adjust_stock_rejects_negative_result() -> None:
    inventory = Inventory(money=100.0, stock={Product.FOOD: 1})

    with pytest.raises(ValueError):
        inventory.adjust_stock(Product.FOOD, -2)

    assert inventory.stock[Product.FOOD] == 1


def test_inventory_string_hides_zero_stock() -> None:
    inventory = Inventory(
        money=12.5,
        stock={Product.FOOD: 0, Product.WOOD: 2},
    )

    assert str(inventory) == "[Money: 12.50 Credits | Stock: Wood: 2]"


def test_execute_production_applies_cost_multiplier() -> None:
    """A multiplier changes credits but not required material quantities."""
    inventory = Inventory(
        money=10.0,
        stock={Product.ORE: 2},
    )

    total_cost = inventory.execute_production(
        product=Product.METAL,
        quantity=1,
        recipe=PRODUCTION_RECIPES[Product.METAL],
        cost_multiplier=0.75,
    )

    assert total_cost == pytest.approx(1.50)
    assert inventory.money == pytest.approx(8.50)
    assert inventory.stock[Product.ORE] == 0
    assert inventory.stock[Product.METAL] == 1


@pytest.mark.parametrize("multiplier", [0, -0.1, 1.1])
def test_execute_production_rejects_invalid_cost_multiplier(
    multiplier: float,
) -> None:
    """Production accepts only positive non-increasing cost multipliers."""
    inventory = Inventory(
        money=10.0,
        stock={Product.ORE: 2},
    )

    with pytest.raises(ValueError, match="cost multiplier"):
        inventory.execute_production(
            product=Product.METAL,
            quantity=1,
            recipe=PRODUCTION_RECIPES[Product.METAL],
            cost_multiplier=multiplier,
        )
