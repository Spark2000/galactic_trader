"""Tests for economy engine and round progression."""

import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import NotEnoughMoneyException, NotProducibleException
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model


@pytest.fixture
def engine() -> EconomyEngine:
    """Creates a deterministic engine without random market events."""
    result = EconomyEngine(random_seed=42, event_probability=0)
    result.player.money = 10_000.0
    result.fleet.add_ship(get_ship_model("standard_s_1"))
    return result


def test_engine_creates_market_for_every_product(engine: EconomyEngine) -> None:
    assert set(engine.markets) == set(Product)


def test_markets_use_product_starting_values(engine: EconomyEngine) -> None:
    food_market = engine.markets[Product.FOOD]

    assert food_market.current_price == Product.FOOD.starting_price
    assert food_market.volatility == Product.FOOD.starting_volatility


def test_buy_does_not_change_price_before_next_round(engine: EconomyEngine) -> None:
    starting_price = engine.markets[Product.WOOD].current_price

    engine.buy_product(Product.WOOD, quantity=1, ship_id=1)

    assert engine.markets[Product.WOOD].current_price == starting_price


def test_sell_does_not_change_price_before_next_round(engine: EconomyEngine) -> None:
    engine.player.stock[Product.WOOD] = 1
    starting_price = engine.markets[Product.WOOD].current_price

    engine.sell_product(Product.WOOD, quantity=1)

    assert engine.markets[Product.WOOD].current_price == starting_price


def test_failed_trade_does_not_change_price_before_next_round(
    engine: EconomyEngine,
) -> None:
    engine.player.money = 0.0

    with pytest.raises(NotEnoughMoneyException):
        engine.buy_product(product=Product.WOOD, quantity=1, ship_id=1)

    assert engine.pending_price_directions[Product.WOOD] == 0
    assert engine.history == []


def test_tick_applies_pending_trade_and_market_trend(engine: EconomyEngine) -> None:
    market = engine.markets[Product.WOOD]
    starting_price = market.current_price
    volatility = market.volatility
    engine.buy_product(product=Product.WOOD, quantity=1, ship_id=1)

    engine.tick()

    expected_price = round(
        starting_price + volatility + engine.last_effective_market_trend,
        2,
    )

    assert market.current_price == pytest.approx(expected_price)


def test_trade_quantity_scales_pending_price_effect(engine: EconomyEngine) -> None:
    product = Product.NAILS
    quantity = 3
    market = engine.markets[product]
    starting_price = market.current_price

    engine.buy_product(product=product, quantity=quantity, ship_id=1)
    engine.tick()

    expected_price = round(
        starting_price
        + quantity * market.volatility
        + engine.last_effective_market_trend,
        2,
    )
    assert market.current_price == pytest.approx(expected_price)


def test_tick_resets_pending_trade_effect(engine: EconomyEngine) -> None:
    engine.buy_product(Product.WOOD, quantity=1, ship_id=1)

    engine.tick()

    price_after_first_tick = engine.markets[Product.FOOD].current_price

    engine.tick()

    expected_price = round(
        price_after_first_tick + engine.last_effective_market_trend,
        2,
    )

    assert engine.markets[Product.FOOD].current_price == pytest.approx(expected_price)
    assert engine.pending_price_directions[Product.FOOD] == 0


def test_produce_product_updates_inventory_and_history(engine: EconomyEngine) -> None:
    product = Product.FURNITURE
    quantity = 2
    recipe = PRODUCTION_RECIPES[product]
    for material, amount_per_unit in recipe.materials.items():
        engine.player.stock[material] = amount_per_unit * quantity
    starting_money = engine.player.money

    action, total_cost = engine.produce_product(product, quantity)

    assert action == "PRODUCE"
    assert total_cost == pytest.approx(recipe.cost * quantity)
    assert engine.player.money == pytest.approx(starting_money - total_cost)
    assert engine.player.stock[product] == quantity
    for material in recipe.materials:
        assert engine.player.stock[material] == 0
    assert engine.history[-1] == (
        action,
        str(product),
        quantity,
        total_cost,
    )


def test_product_without_recipe_cannot_be_produced(engine: EconomyEngine) -> None:
    with pytest.raises(NotProducibleException):
        engine.produce_product(Product.FOOD, 1)

    assert engine.history == []
