"""Tests for randomized trends and events during round progression."""

import pytest

from galactic_trader.engine import (
    TREND_MULTIPLIER_MAX,
    TREND_MULTIPLIER_MIN,
    EconomyEngine,
)
from galactic_trader.products import Product


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
