from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product


def test_engine_creates_market_for_every_product() -> None:
    engine = EconomyEngine()

    assert set(engine.markets) == set(Product)


def test_markets_use_product_starting_values() -> None:
    engine = EconomyEngine()

    food_market = engine.markets[Product.FOOD]

    assert food_market.current_price == Product.FOOD.starting_price
    assert food_market.volatility == Product.FOOD.starting_volatility
