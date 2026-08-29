import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product


@pytest.fixture
def engine() -> EconomyEngine:
    return EconomyEngine()


def test_engine_creates_market_for_every_product(engine: EconomyEngine) -> None:
    assert set(engine.markets) == set(Product)


def test_markets_use_product_starting_values(engine: EconomyEngine) -> None:
    food_market = engine.markets[Product.FOOD]

    assert food_market.current_price == Product.FOOD.starting_price
    assert food_market.volatility == Product.FOOD.starting_volatility


def test_trade_does_not_change_price_before_next_round(engine: EconomyEngine) -> None:
    starting_price = engine.markets[Product.FOOD].current_price

    engine.interact_with_market(is_buy=True, product=Product.FOOD, quantity=1)

    assert engine.markets[Product.FOOD].current_price == starting_price


def test_sell_does_not_change_price_before_next_round(engine: EconomyEngine) -> None:
    engine.player.stock[Product.FOOD] = 1
    starting_price = engine.markets[Product.FOOD].current_price

    engine.interact_with_market(is_buy=False, product=Product.FOOD, quantity=1)

    assert engine.markets[Product.FOOD].current_price == starting_price


def test_tick_applies_pending_trade_and_market_trend(engine: EconomyEngine) -> None:
    starting_price = engine.markets[Product.FOOD].current_price
    volatility = engine.markets[Product.FOOD].volatility
    trend = engine.current_market_trend
    engine.interact_with_market(is_buy=True, product=Product.FOOD, quantity=1)

    engine.tick()

    expected_price = round(starting_price + volatility + trend, 2)

    assert engine.markets[Product.FOOD].current_price == pytest.approx(expected_price)


def test_tick_resets_pending_trade_effect(engine: EconomyEngine) -> None:
    engine.interact_with_market(is_buy=True, product=Product.FOOD, quantity=1)

    engine.tick()

    price_after_first_tick = engine.markets[Product.FOOD].current_price
    trend_second = engine.current_market_trend

    engine.tick()

    expected_price = round(price_after_first_tick + trend_second, 2)

    assert engine.markets[Product.FOOD].current_price == pytest.approx(expected_price)
