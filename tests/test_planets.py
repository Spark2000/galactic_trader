"""Tests for immutable planet definitions."""

import pytest

from galactic_trader.planets import Planet, PlanetInfo


def test_every_planet_has_valid_information() -> None:
    """Every registered planet exposes usable display and travel data."""
    for planet in Planet:
        assert planet.display_name
        assert planet.description
        assert planet.distance > 0
        assert str(planet) == planet.display_name


@pytest.mark.parametrize(
    ("display_name", "description", "distance", "error_message"),
    [
        ("", "A valid description.", 10, "display name"),
        ("Valid", "  ", 10, "description"),
        ("Valid", "A valid description.", 0, "distance"),
        ("Valid", "A valid description.", -1, "distance"),
    ],
)
def test_planet_info_rejects_invalid_values(
    display_name: str,
    description: str,
    distance: int,
    error_message: str,
) -> None:
    """Invalid fixed planet values are rejected during construction."""
    with pytest.raises(ValueError, match=error_message):
        PlanetInfo(display_name, description, distance)
