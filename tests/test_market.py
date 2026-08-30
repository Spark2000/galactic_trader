"""Tests for market validation and price adjustments."""

import pytest

from galactic_trader.market import Market
from galactic_trader.products import Product


def test_initial_current_price_value_too_low() -> None:
    with pytest.raises(ValueError):
        Market(product=Product.FOOD, current_price=0.5, volatility=0.5)


def test_initial_volatility_value_too_low() -> None:
    with pytest.raises(ValueError):
        Market(product=Product.FOOD, current_price=10.0, volatility=-1)


def test_set_price() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.set_price(3.0)

    assert market.current_price == 3.0


def test_set_price_too_low() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.set_price(0.3)

    assert market.current_price == 1.0


def test_set_volatility() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.set_volatility(0.8)

    assert market.volatility == 0.8


def test_set_volatitlity_too_low() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.set_volatility(-1)

    assert market.volatility == 0.0


def test_adjust_price() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.adjust_price(1)

    assert market.current_price == 10.5


def test_adjust_price_uses_quantity_as_direction() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.adjust_price(-3)

    assert market.current_price == 8.5


def test_set_price_rounds_to_two_decimal_places() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.set_price(3.456)

    assert market.current_price == 3.46


def test_adjust_volatility() -> None:
    market = Market(product=Product.FOOD, current_price=10.0, volatility=0.5)

    market.adjust_volatility(-1)

    assert market.volatility == 0.0
