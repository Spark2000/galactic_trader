"""Tests for randomized trends and events during round progression."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.engine import (
    TREND_MULTIPLIER_MAX,
    TREND_MULTIPLIER_MIN,
    EconomyEngine,
)
from galactic_trader.products import Product
from galactic_trader.ships import ShipModel


def test_tick_uses_small_random_multiplier_for_periodic_trend() -> None:
    engine = EconomyEngine(random_seed=42, event_probability=0)
    market = engine.markets[Product.FOOD]
    starting_price = market.current_price
    base_trend = engine.current_market_trend

    result = engine.tick()

    assert result.market_event is None
    assert TREND_MULTIPLIER_MIN <= engine.last_trend_multiplier
    assert engine.last_trend_multiplier <= TREND_MULTIPLIER_MAX
    assert engine.last_effective_market_trend == pytest.approx(
        base_trend * engine.last_trend_multiplier
    )
    assert market.current_price == pytest.approx(
        round(starting_price + engine.last_effective_market_trend, 2)
    )


def test_same_seed_reproduces_trends_events_and_prices() -> None:
    first = EconomyEngine(random_seed=123, event_probability=1)
    second = EconomyEngine(random_seed=123, event_probability=1)

    first_res = first.tick()
    second_res = second.tick()

    assert first.last_trend_multiplier == second.last_trend_multiplier
    assert first_res == second_res
    assert {
        product: market.current_price for product, market in first.markets.items()
    } == {product: market.current_price for product, market in second.markets.items()}


def test_event_probability_zero_keeps_round_free_of_events() -> None:
    engine = EconomyEngine(random_seed=7, event_probability=0)

    result = engine.tick()

    assert result.market_event is None
    assert engine.last_market_event is None


def test_event_probability_one_triggers_and_stores_event() -> None:
    engine = EconomyEngine(random_seed=7, event_probability=1)

    result = engine.tick()

    assert result.market_event is not None
    assert engine.last_market_event == result.market_event
    assert result.market_event.message


@pytest.mark.parametrize("probability", [-0.01, 1.01])
def test_engine_rejects_invalid_event_probability(probability: float) -> None:
    with pytest.raises(ValueError):
        EconomyEngine(event_probability=probability)


"""BELOW ARE TESTS REGARDING TRANSPORT EVENTS (PIRAT ATTACK)"""


def make_ship_model(*, defense_rating: int) -> ShipModel:
    """Create a fast standard-cargo test model with configurable defense."""
    return ShipModel(
        model_id=f"pirate_test_{defense_rating}",
        display_name="Pirate Test Ship",
        cargo_type=CargoType.STANDARD,
        cargo_capacity=10,
        speed_rating=100,
        defense_rating=defense_rating,
        purchase_price=1.0,
    )


@pytest.mark.parametrize("probability", [-0.01, 1.01])
def test_engine_rejects_invalid_pirate_probability(
    probability: float,
) -> None:
    """The configured attack probability must be a valid probability."""
    with pytest.raises(ValueError, match="Pirate attack probability"):
        EconomyEngine(pirate_attack_probability=probability)


def test_full_theft_returns_ship_without_delivering_stock() -> None:
    """A completely robbed ship finishes its journey and becomes available."""
    engine = EconomyEngine(
        random_seed=1,
        event_probability=0,
        pirate_attack_probability=1,
    )
    ship = engine.fleet.add_ship(make_ship_model(defense_rating=0))
    purchase = engine.buy_product(
        Product.GEMS,
        quantity=1,
        ship_id=ship.ship_id,
    )

    assert purchase.travel_rounds == 2

    first_round = engine.tick()

    assert first_round.pirate_attack is not None
    assert not first_round.pirate_attack.defended
    assert first_round.pirate_attack.stolen_quantity == 1
    assert first_round.completed_deliveries == ()
    assert not ship.is_available

    second_round = engine.tick()

    assert second_round.pirate_attack is None
    assert len(second_round.completed_deliveries) == 1
    assert second_round.completed_deliveries[0].quantity == 0
    assert "returned without cargo" in (second_round.completed_deliveries[0].message)
    assert engine.player.stock.get(Product.GEMS, 0) == 0
    assert ship.is_available


def test_probability_zero_preserves_normal_delivery() -> None:
    """Disabling pirate attacks retains the existing transport behavior."""
    engine = EconomyEngine(
        random_seed=1,
        event_probability=0,
        pirate_attack_probability=0,
    )
    ship = engine.fleet.add_ship(make_ship_model(defense_rating=0))
    purchase = engine.buy_product(
        Product.GEMS,
        quantity=2,
        ship_id=ship.ship_id,
    )

    for _ in range(purchase.travel_rounds - 1):
        result = engine.tick()
        assert result.pirate_attack is None
        assert result.completed_deliveries == ()

    result = engine.tick()

    assert result.pirate_attack is None
    assert result.completed_deliveries[0].quantity == 2
    assert engine.player.stock[Product.GEMS] == 2
