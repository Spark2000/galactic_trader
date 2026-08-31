"""Tests for buying and selling individual spaceships."""

import pytest

from galactic_trader.engine import SHIP_RESALE_RATE, EconomyEngine
from galactic_trader.exceptions import (
    NotEnoughMoneyException,
    ShipNotOwnedException,
    UnknownShipModelException,
)


@pytest.fixture
def engine() -> EconomyEngine:
    """Create a deterministic engine without random events."""
    return EconomyEngine(random_seed=42, event_probability=0)


def test_buy_ship_deducts_money_and_adds_owned_ship(
    engine: EconomyEngine,
) -> None:
    starting_money = engine.player.money

    owned_ship, purchase_price = engine.buy_ship("standard_s_1")

    assert purchase_price == pytest.approx(80.0)
    assert engine.player.money == pytest.approx(starting_money - purchase_price)
    assert engine.fleet.ships == (owned_ship,)
    assert engine.history[-1] == (
        "BUY_SHIP",
        "Comet Courier (ID: #1)",
        1,
        purchase_price,
    )


def test_buy_same_model_three_times_creates_distinct_ships(
    engine: EconomyEngine,
) -> None:
    engine.player.money = 5000.0

    ships = [engine.buy_ship("atlas_runner")[0] for _ in range(3)]

    assert [ship.ship_id for ship in ships] == [1, 2, 3]
    assert len(engine.fleet) == 3
    assert ships[0].model is ships[1].model is ships[2].model


def test_failed_purchase_does_not_change_money_fleet_or_history(
    engine: EconomyEngine,
) -> None:
    engine.player.money = 0.0
    starting_money = engine.player.money

    with pytest.raises(NotEnoughMoneyException):
        engine.buy_ship("atlas_runner")

    assert engine.player.money == starting_money
    assert engine.fleet.ships == ()
    assert engine.history == []


def test_unknown_model_does_not_change_state(engine: EconomyEngine) -> None:
    starting_money = engine.player.money

    with pytest.raises(UnknownShipModelException):
        engine.buy_ship("unknown_ship")

    assert engine.player.money == starting_money
    assert engine.fleet.ships == ()
    assert engine.history == []


def test_sell_ship_removes_instance_and_credits_resale_value(
    engine: EconomyEngine,
) -> None:
    engine.player.money = 5000.0
    owned_ship, purchase_price = engine.buy_ship("atlas_runner")
    money_before_sale = engine.player.money

    sold_ship, sale_price = engine.sell_ship(owned_ship.ship_id)

    assert sold_ship is owned_ship
    assert sale_price == pytest.approx(purchase_price * SHIP_RESALE_RATE)
    assert engine.player.money == pytest.approx(money_before_sale + sale_price)
    assert engine.fleet.ships == ()
    assert engine.history[-1] == (
        "SELL_SHIP",
        "Atlas Runner (ID: #1)",
        1,
        sale_price,
    )


def test_sell_one_duplicate_keeps_other_instances(
    engine: EconomyEngine,
) -> None:
    engine.player.money = 5000.0
    first = engine.buy_ship("atlas_runner")[0]
    second = engine.buy_ship("atlas_runner")[0]
    third = engine.buy_ship("atlas_runner")[0]

    engine.sell_ship(second.ship_id)

    assert engine.fleet.ships == (first, third)


def test_failed_sale_does_not_change_money_fleet_or_history(
    engine: EconomyEngine,
) -> None:
    starting_money = engine.player.money

    with pytest.raises(ShipNotOwnedException):
        engine.sell_ship(999)

    assert engine.player.money == starting_money
    assert engine.fleet.ships == ()
    assert engine.history == []
