import pytest

from galactic_trader.exceptions import NotEnoughMoneyException, NotEnoughStockException
from galactic_trader.inventory import Inventory
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
