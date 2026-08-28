import pytest

from galactic_trader.exceptions import *
from galactic_trader.inventory import *


def test_buying_reduces_money_and_increases_stock() -> None:
    inv = Inventory(money=100.0)

    inv.execute_trade(product=ProductType.FOOD, quantity=2, unit_price=10.0)

    assert inv.money == 80.0
    assert inv.stock[ProductType.FOOD] == 2


def test_buying_without_enough_money() -> None:
    inv = Inventory(money=2.0)

    with pytest.raises(NotEnoughMoneyException):
        inv.execute_trade(product=ProductType.FOOD, quantity=1, unit_price=10.0)


def test_selling_increases_money_and_reduces_stock() -> None:
    inv = Inventory(money=100.0)
    inv.stock[ProductType.FOOD] = 3

    inv.execute_trade(product=ProductType.FOOD, quantity=-2, unit_price=10.0)

    assert inv.money == 120.0
    assert inv.stock[ProductType.FOOD] == 1


def test_selling_without_enough_stock() -> None:
    inv = Inventory(money=100.0)

    with pytest.raises(NotEnoughStockException):
        inv.execute_trade(product=ProductType.FOOD, quantity=-1, unit_price=10.0)
