"""Tests for transport data objects."""

import pytest

from galactic_trader.products import Product
from galactic_trader.transport import TransportMission


def test_transport_advances_until_completion() -> None:
    mission = TransportMission(
        product=Product.WOOD,
        quantity=3,
        total_rounds=2,
        remaining_rounds=2,
    )

    assert not mission.advance()
    assert mission.remaining_rounds == 1
    assert mission.advance()
    assert mission.remaining_rounds == 0


def test_completed_transport_cannot_advance_again() -> None:
    mission = TransportMission(
        product=Product.WOOD,
        quantity=1,
        total_rounds=1,
        remaining_rounds=1,
    )
    mission.advance()

    with pytest.raises(RuntimeError):
        mission.advance()


@pytest.mark.parametrize(
    ("quantity", "total_rounds", "remaining_rounds"),
    [
        (0, 1, 1),
        (1, 0, 1),
        (1, 2, 0),
        (1, 2, 3),
    ],
)
def test_transport_rejects_invalid_initial_state(
    quantity: int,
    total_rounds: int,
    remaining_rounds: int,
) -> None:
    with pytest.raises(ValueError):
        TransportMission(
            product=Product.WOOD,
            quantity=quantity,
            total_rounds=total_rounds,
            remaining_rounds=remaining_rounds,
        )
