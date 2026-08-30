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


def test_buying_reduces_money_and_increases_stock() -> None:
    inv = Inventory(money=100.0)

    inv.execute_trade(product=Product.FOOD, quantity=2, unit_price=10.0)

    assert inv.money == 80.0
    assert inv.stock[Product.FOOD] == 2


def test_buying_without_enough_money() -> None:
    inv = Inventory(money=2.0)

    with pytest.raises(NotEnoughMoneyException):
        inv.execute_trade(product=Product.FOOD, quantity=1, unit_price=10.0)


def test_selling_increases_money_and_reduces_stock() -> None:
    inv = Inventory(money=100.0)
    inv.stock[Product.FOOD] = 3

    inv.execute_trade(product=Product.FOOD, quantity=-2, unit_price=10.0)

    assert inv.money == 120.0
    assert inv.stock[Product.FOOD] == 1


def test_selling_without_enough_stock() -> None:
    inv = Inventory(money=100.0)

    with pytest.raises(NotEnoughStockException):
        inv.execute_trade(product=Product.FOOD, quantity=-1, unit_price=10.0)


@pytest.mark.parametrize(
    ("quantity", "unit_price"),
    [
        (0, 10.0),
        (1, 0.0),
        (1, -1.0),
    ],
)
def test_trade_rejects_invalid_contract_values(
    quantity: int, unit_price: float
) -> None:
    inventory = Inventory(money=100.0)

    with pytest.raises(AssertionError):
        inventory.execute_trade(Product.FOOD, quantity, unit_price)


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
