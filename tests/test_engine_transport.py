"""Tests for product purchases, transport progress, and delivery."""

import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import (
    IncompatibleCargoException,
    NotEnoughCargoCapacityException,
    NotEnoughMoneyException,
    ShipInTransitException,
)
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model


@pytest.fixture
def engine() -> EconomyEngine:
    """Create a deterministic engine with enough money for feature tests."""
    result = EconomyEngine(random_seed=42, event_probability=0)
    result.player.money = 10_000.0
    return result


def add_ship(engine: EconomyEngine, model_id: str) -> int:
    """Add a ship without making its purchase part of the tested action."""
    return engine.fleet.add_ship(get_ship_model(model_id)).ship_id


def test_purchase_deducts_money_but_does_not_fill_stock(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    starting_money = engine.player.money

    product = Product.WOOD
    market = engine.markets[product]
    quantity = 5

    purchase = engine.buy_product(product=product, quantity=quantity, ship_id=ship_id)

    assert purchase.total_cost == pytest.approx(market.current_price * quantity)
    assert engine.player.money == pytest.approx(starting_money - (market.current_price * quantity))
    assert engine.player.stock.get(product, 0) == 0
    ship = engine.fleet.get_ship(ship_id)
    assert ship.active_transport is not None
    assert ship.active_transport.quantity == quantity
    assert engine.pending_price_directions[product] == 5
    assert engine.history[-1] == ("BUY", product.display_name, quantity, 8.0)


def test_delivery_arrives_only_after_all_travel_rounds(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    purchase = engine.buy_product(
        Product.GEMS,
        quantity=1,
        ship_id=ship_id,
    )

    assert purchase.travel_rounds == 2
    assert engine.player.stock.get(Product.GEMS, 0) == 0

    # product is still on its way.
    for _ in range(purchase.travel_rounds - 1):
        result = engine.tick()

        assert result.completed_deliveries == ()
        assert engine.player.stock.get(Product.GEMS, 0) == 0

    # product is being delivered in last tick.
    result = engine.tick()

    assert len(result.completed_deliveries) == 1
    delivery = result.completed_deliveries[0]

    assert delivery.product is Product.GEMS
    assert delivery.quantity == 1
    assert delivery.ship_id == ship_id
    assert engine.player.stock[Product.GEMS] == 1


def test_transport_options_include_only_eligible_ships(
    engine: EconomyEngine,
) -> None:
    small_id = add_ship(engine, "standard_s_1")
    medium_id = add_ship(engine, "standard_m_1")
    add_ship(engine, "refrigerated_s_1")
    engine.buy_product(Product.WOOD, quantity=1, ship_id=small_id)

    options = engine.get_transport_options(Product.WOOD, quantity=20)

    assert [option.ship_id for option in options] == [medium_id]
    assert options[0].travel_rounds == 1


def test_incompatible_ship_rejects_purchase_atomically(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "refrigerated_s_1")
    state_before = (
        engine.player.money,
        engine.player.stock.copy(),
        engine.history.copy(),
    )

    with pytest.raises(IncompatibleCargoException):
        engine.buy_product(Product.WOOD, quantity=1, ship_id=ship_id)

    assert state_before == (
        engine.player.money,
        engine.player.stock,
        engine.history,
    )
    assert engine.fleet.get_ship(ship_id).is_available


def test_insufficient_capacity_rejects_purchase_atomically(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    starting_money = engine.player.money

    with pytest.raises(NotEnoughCargoCapacityException):
        engine.buy_product(Product.WOOD, quantity=11, ship_id=ship_id)

    assert engine.player.money == starting_money
    assert engine.history == []
    assert engine.fleet.get_ship(ship_id).is_available


def test_busy_ship_rejects_second_purchase_atomically(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    engine.buy_product(Product.WOOD, quantity=1, ship_id=ship_id)
    money_after_first_purchase = engine.player.money
    history_after_first_purchase = engine.history.copy()

    with pytest.raises(ShipInTransitException):
        engine.buy_product(Product.ORE, quantity=1, ship_id=ship_id)

    assert engine.player.money == money_after_first_purchase
    assert engine.history == history_after_first_purchase
    assert engine.player.stock.get(Product.ORE, 0) == 0


def test_insufficient_money_rejects_purchase_atomically(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    engine.player.money = 0.0

    with pytest.raises(NotEnoughMoneyException):
        engine.buy_product(Product.WOOD, quantity=1, ship_id=ship_id)

    assert engine.player.money == 0.0
    assert engine.history == []
    assert engine.pending_price_directions[Product.WOOD] == 0
    assert engine.fleet.get_ship(ship_id).is_available


def test_product_price_waits_for_tick_after_transport_purchase(
    engine: EconomyEngine,
) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    market = engine.markets[Product.WOOD]
    starting_price = market.current_price

    engine.buy_product(Product.WOOD, quantity=2, ship_id=ship_id)

    assert market.current_price == starting_price
    engine.tick()
    expected_price = round(
        starting_price
        + 2 * market.volatility
        + engine.last_effective_market_trend,
        2,
    )
    assert market.current_price == pytest.approx(expected_price)


def test_ship_in_transit_cannot_be_sold(engine: EconomyEngine) -> None:
    ship_id = add_ship(engine, "standard_s_1")
    engine.buy_product(Product.GEMS, quantity=1, ship_id=ship_id)
    money_before_sale = engine.player.money

    with pytest.raises(ShipInTransitException):
        engine.sell_ship(ship_id)

    assert engine.player.money == money_before_sale
    assert engine.fleet.get_ship(ship_id).ship_id == ship_id


def test_selling_products_changes_stock_immediately(
    engine: EconomyEngine,
) -> None:
    engine.player.stock[Product.WOOD] = 3
    starting_money = engine.player.money

    action, unit_price = engine.sell_product(Product.WOOD, quantity=2)

    assert action == "SELL"
    assert engine.player.stock[Product.WOOD] == 1
    assert engine.player.money == pytest.approx(
        starting_money + 2 * unit_price
    )
