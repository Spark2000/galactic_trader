"""Tests for market event definitions and effects."""

from random import Random

import pytest

from galactic_trader.events import (
    MARKET_EVENTS,
    MarketEvent,
    choose_market_event,
)
from galactic_trader.market import Market
from galactic_trader.products import Product


def create_markets() -> dict[Product, Market]:
    """Creates a market with starting values for every product."""
    return {
        product: Market(
            product=product,
            current_price=product.starting_price,
            volatility=product.starting_volatility,
        )
        for product in Product
    }


def test_single_product_event_changes_only_affected_market() -> None:
    markets = create_markets()
    starting_prices = {
        product: market.current_price for product, market in markets.items()
    }
    event = MarketEvent(
        name="Test drought",
        description="Food becomes scarce.",
        affected_products=(Product.FOOD,),
        direction=1,
        min_percentage=0.10,
        max_percentage=0.10,
    )

    occurrence = event.apply(markets, Random(1))

    assert occurrence.percentage_change == pytest.approx(0.10)
    assert markets[Product.FOOD].current_price == pytest.approx(
        starting_prices[Product.FOOD] * 1.10
    )
    for product in Product:
        if product is not Product.FOOD:
            assert markets[product].current_price == starting_prices[product]


def test_global_negative_event_changes_every_market_by_same_percentage() -> None:
    markets = create_markets()
    event = MarketEvent(
        name="Test agreement",
        description="Goods become cheaper.",
        affected_products=tuple(Product),
        direction=-1,
        min_percentage=0.05,
        max_percentage=0.05,
    )

    occurrence = event.apply(markets, Random(2))

    assert occurrence.percentage_change == pytest.approx(-0.05)
    for product, market in markets.items():
        expected_price = round(product.starting_price * 0.95, 2)
        assert market.current_price == pytest.approx(max(1.0, expected_price))


def test_event_message_contains_name_products_and_effect() -> None:
    markets = create_markets()
    event = MarketEvent(
        name="Drought",
        description="Food becomes scarce.",
        affected_products=(Product.FOOD,),
        direction=1,
        min_percentage=0.10,
        max_percentage=0.10,
    )

    message = event.apply(markets, Random(3)).message

    assert "Drought" in message
    assert "Food" in message
    assert "increased by 10.0%" in message


def test_zero_probability_selects_no_event() -> None:
    assert choose_market_event(Random(4), event_probability=0) is None


def test_certain_probability_selects_an_available_event() -> None:
    selected_event = choose_market_event(Random(5), event_probability=1)

    assert selected_event in MARKET_EVENTS


@pytest.mark.parametrize("probability", [-0.01, 1.01])
def test_event_selection_rejects_invalid_probability(probability: float) -> None:
    with pytest.raises(ValueError):
        choose_market_event(Random(6), event_probability=probability)


@pytest.mark.parametrize(
    ("direction", "minimum", "maximum"),
    [
        (0, 0.05, 0.10),
        (1, 0.00, 0.10),
        (1, 0.11, 0.10),
        (1, 0.05, 0.21),
    ],
)
def test_market_event_rejects_invalid_configuration(
    direction: int,
    minimum: float,
    maximum: float,
) -> None:
    with pytest.raises(ValueError):
        MarketEvent(
            name="Invalid",
            description="Invalid test event.",
            affected_products=(Product.FOOD,),
            direction=direction,
            min_percentage=minimum,
            max_percentage=maximum,
        )
