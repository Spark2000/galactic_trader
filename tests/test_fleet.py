"""Tests for individual spaceship ownership and fleet management."""

import pytest

from galactic_trader.exceptions import ShipInTransitException, ShipNotOwnedException
from galactic_trader.fleet import Fleet
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model
from galactic_trader.transport import TransportMission


def test_same_model_can_be_owned_multiple_times() -> None:
    fleet = Fleet()
    model = get_ship_model("atlas_runner")

    first = fleet.add_ship(model)
    second = fleet.add_ship(model)
    third = fleet.add_ship(model)

    assert [ship.ship_id for ship in fleet.ships] == [1, 2, 3]
    assert first.model is second.model is third.model


def test_remove_ship_removes_only_requested_instance() -> None:
    fleet = Fleet()
    model = get_ship_model("atlas_runner")
    first = fleet.add_ship(model)
    second = fleet.add_ship(model)
    third = fleet.add_ship(model)

    removed = fleet.remove_ship(second.ship_id)

    assert removed is second
    assert fleet.ships == (first, third)


def test_ship_ids_are_not_reused_after_sale() -> None:
    fleet = Fleet()
    model = get_ship_model("standard_s_1")
    first = fleet.add_ship(model)
    fleet.add_ship(model)
    fleet.remove_ship(first.ship_id)

    next_ship = fleet.add_ship(model)

    assert next_ship.ship_id == 3


def test_unknown_owned_ship_id_is_rejected() -> None:
    fleet = Fleet()

    with pytest.raises(ShipNotOwnedException):
        fleet.get_ship(999)


def create_mission(rounds: int = 2) -> TransportMission:
    """Create a standard-cargo transport mission for a test."""
    return TransportMission(
        product=Product.WOOD,
        quantity=2,
        total_rounds=rounds,
        remaining_rounds=rounds,
    )


def test_available_ships_match_status_cargo_type_and_capacity() -> None:
    fleet = Fleet()
    small_standard = fleet.add_ship(get_ship_model("standard_s_1"))
    medium_standard = fleet.add_ship(get_ship_model("standard_m_1"))
    fleet.add_ship(get_ship_model("refrigerated_s_1"))
    small_standard.start_transport(create_mission())

    available = fleet.get_available_ships(Product.WOOD, quantity=20)

    assert available == (medium_standard,)


def test_completed_transport_makes_ship_available_again() -> None:
    fleet = Fleet()
    ship = fleet.add_ship(get_ship_model("standard_s_1"))
    ship.start_transport(create_mission(rounds=1))

    completed = ship.advance_transport()

    assert completed is not None
    assert completed.product is Product.WOOD
    assert ship.is_available


def test_ship_in_transit_cannot_be_removed() -> None:
    fleet = Fleet()
    ship = fleet.add_ship(get_ship_model("standard_s_1"))
    ship.start_transport(create_mission())

    with pytest.raises(ShipInTransitException):
        fleet.remove_ship(ship.ship_id)

    assert fleet.ships == (ship,)
