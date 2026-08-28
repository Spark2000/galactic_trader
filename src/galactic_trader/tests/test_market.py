from galactic_trader.market import *


def test_adjust_price() -> None:
    market = Market(product=ProductType.FOOD, current_price=10.0, volatility=0.5)

    market.adjust_price(1)

    assert market.current_price == 10.5

def test_adjust_price_below_one() -> None:
    market = Market(product=ProductType.FOOD, current_price=10.0, volatility=9.5)

    market.adjust_price(-1)

    assert market.current_price == 1.0