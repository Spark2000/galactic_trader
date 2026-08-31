"""Unit tests for pirate attacks on active transports."""

from collections.abc import Sequence
from random import Random
from typing import TypeVar, cast

from galactic_trader.cargo import CargoType
from galactic_trader.events_transport import resolve_pirate_attack
from galactic_trader.fleet import Fleet, OwnedShip
from galactic_trader.products import Product
from galactic_trader.ships import ShipModel
from galactic_trader.transport import TransportMission

T = TypeVar("T")


class StubRandom:
    """Supply deterministic random results to pirate-event tests."""

    def __init__(
        self,
        *,
        rolls: list[float],
        choice_index: int = 0,
        loss_percentage: int = 30,
    ) -> None:
        """Store results returned by random operations in call order."""
        self._rolls = iter(rolls)
        self.choice_index = choice_index
        self.loss_percentage = loss_percentage

    def random(self) -> float:
        """Return the next configured probability roll."""
        return next(self._rolls)

    def choice(self, values: Sequence[T]) -> T:
        """Return the configured item from a non-empty sequence."""
        return values[self.choice_index]

    def randint(self, start: int, end: int) -> int:
        """Return the configured loss percentage within the requested range."""
        assert start <= self.loss_percentage <= end
        return self.loss_percentage


def add_transport(
    fleet: Fleet,
    *,
    model_id: str,
    defense_rating: int,
    quantity: int = 10,
) -> OwnedShip:
    """Add a test ship and assign a standard-cargo transport mission."""
    model = ShipModel(
        model_id=model_id,
        display_name=model_id.replace("_", " ").title(),
        cargo_type=CargoType.STANDARD,
        cargo_capacity=quantity,
        speed_rating=50,
        defense_rating=defense_rating,
        purchase_price=1.0,
    )
    ship = fleet.add_ship(model)
    ship.start_transport(
        TransportMission(
            product=Product.GEMS,
            quantity=quantity,
            total_rounds=2,
            remaining_rounds=2,
        )
    )
    return ship


def as_random(stub: StubRandom) -> Random:
    """Cast the deterministic test double to the production Random type."""
    return cast(Random, stub)


def test_no_attack_occurs_without_a_cargo_bearing_transport() -> None:
    """A guaranteed attack still requires at least one valid target."""
    result = resolve_pirate_attack(
        fleet=Fleet(),
        random_generator=as_random(StubRandom(rolls=[])),
        probability=1,
    )

    assert result is None


def test_defense_rating_one_hundred_always_repels_attack() -> None:
    """Maximum defense leaves the complete transport cargo untouched."""
    fleet = Fleet()
    ship = add_transport(
        fleet,
        model_id="perfect_defense",
        defense_rating=100,
    )

    result = resolve_pirate_attack(
        fleet=fleet,
        random_generator=as_random(StubRandom(rolls=[0.0, 0.999999])),
        probability=1,
    )

    assert result is not None
    assert result.defended
    assert result.stolen_quantity == 0
    assert result.loss_percentage is None
    assert ship.active_transport is not None
    assert ship.active_transport.quantity == 10


def test_defense_rating_zero_loses_rounded_up_percentage() -> None:
    """Zero defense loses the configured share rounded up to whole units."""
    fleet = Fleet()
    ship = add_transport(
        fleet,
        model_id="no_defense",
        defense_rating=0,
        quantity=7,
    )

    result = resolve_pirate_attack(
        fleet=fleet,
        random_generator=as_random(
            StubRandom(
                rolls=[0.0, 0.0],
                loss_percentage=31,
            )
        ),
        probability=1,
    )

    assert result is not None
    assert not result.defended
    assert result.stolen_quantity == 3
    assert result.remaining_quantity == 4
    assert ship.active_transport is not None
    assert ship.active_transport.quantity == 4


def test_only_one_randomly_selected_transport_is_attacked() -> None:
    """An attack changes no transport except the selected target."""
    fleet = Fleet()
    first_ship = add_transport(
        fleet,
        model_id="first_target",
        defense_rating=0,
    )
    second_ship = add_transport(
        fleet,
        model_id="second_target",
        defense_rating=0,
    )

    result = resolve_pirate_attack(
        fleet=fleet,
        random_generator=as_random(
            StubRandom(
                rolls=[0.0, 0.0],
                choice_index=1,
                loss_percentage=50,
            )
        ),
        probability=1,
    )

    assert result is not None
    assert result.ship_id == second_ship.ship_id
    assert first_ship.active_transport is not None
    assert first_ship.active_transport.quantity == 10
    assert second_ship.active_transport is not None
    assert second_ship.active_transport.quantity == 5


def test_one_hundred_percent_loss_removes_all_cargo() -> None:
    """A maximum-strength theft leaves the mission with zero cargo."""
    fleet = Fleet()
    ship = add_transport(
        fleet,
        model_id="complete_loss",
        defense_rating=0,
        quantity=4,
    )

    result = resolve_pirate_attack(
        fleet=fleet,
        random_generator=as_random(
            StubRandom(
                rolls=[0.0, 0.0],
                loss_percentage=100,
            )
        ),
        probability=1,
    )

    assert result is not None
    assert result.stolen_quantity == 4
    assert result.remaining_quantity == 0
    assert ship.active_transport is not None
    assert ship.active_transport.quantity == 0
