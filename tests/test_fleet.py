"""Tests for individual spaceship ownership and fleet management."""

import pytest

from galactic_trader.exceptions import ShipNotOwnedException
from galactic_trader.fleet import Fleet
from galactic_trader.ships import get_ship_model


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
