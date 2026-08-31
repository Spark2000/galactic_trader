"""Tests for spaceship model definitions and balancing."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.exceptions import UnknownShipModelException
from galactic_trader.planets import Planet
from galactic_trader.products import Product
from galactic_trader.ships import (
    ShipModel,
    get_all_ship_models,
    get_ship_model,
    get_ship_models,
)


def test_model_ids_and_display_names_are_unique() -> None:
    models = get_all_ship_models()
    model_ids = [model.model_id for model in models]
    display_names = [model.display_name for model in models]

    assert len(models) >= 13
    assert len(model_ids) == len(set(model_ids))
    assert len(display_names) == len(set(display_names))


def test_get_ship_model_accepts_normalized_user_input() -> None:
    model = get_ship_model("  ATLAS_RUNNER  ")

    assert model.model_id == "atlas_runner"
    assert model.display_name == "Atlas Runner"


def test_get_ship_model_rejects_unknown_id() -> None:
    with pytest.raises(UnknownShipModelException):
        get_ship_model("unknown_ship")


def test_ship_only_accepts_its_own_cargo_type() -> None:
    standard_model = get_ship_models(CargoType.STANDARD)[0]
    refrigerated_model = get_ship_models(CargoType.REFRIGERATED)[0]

    assert standard_model.can_transport(Product.WOOD)
    assert not standard_model.can_transport(Product.FOOD)
    assert refrigerated_model.can_transport(Product.FOOD)
    assert not refrigerated_model.can_transport(Product.WOOD)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("cargo_capacity", 0),
        ("speed_rating", -1),
        ("speed_rating", 101),
        ("speed_rating", 0),
        ("defense_rating", -1),
        ("defense_rating", 101),
        ("purchase_price", 0),
    ],
)
def test_ship_model_rejects_invalid_values(
    field_name: str,
    invalid_value: int,
) -> None:
    values: dict[str, object] = {
        "model_id": "test_ship",
        "display_name": "Test Ship",
        "cargo_type": CargoType.STANDARD,
        "cargo_capacity": 10,
        "speed_rating": 50,
        "defense_rating": 50,
        "purchase_price": 100.0,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValueError):
        ShipModel(**values)  # type: ignore[arg-type]


def test_calculate_travel_rounds_uses_round_trip_and_rounds_up() -> None:
    model = get_ship_model("standard_s_1")

    assert Product.WOOD.planet is Planet.ENDOR
    assert Product.WOOD.planet.distance == 10
    assert Product.GEMS.planet is Planet.KESSEL
    assert Product.GEMS.planet.distance == 60

    assert model.calculate_travel_rounds_to(Planet.ENDOR) == 1
    assert model.calculate_travel_rounds_to(Planet.KESSEL) == 2


@pytest.mark.parametrize(
    ("planet", "expected_rounds"),
    [
        (Planet.ALDERAAN, 1),
        (Planet.KESSEL, 2),
        (Planet.CORUSCANT, 3),
        (Planet.GEONOSIS, 4),
    ],
)
def test_calculate_travel_rounds_to_planet(
    planet: Planet,
    expected_rounds: int,
) -> None:
    """Round-trip distance is divided by speed and rounded upward."""
    model = get_ship_model("standard_s_1")

    assert model.calculate_travel_rounds_to(planet) == expected_rounds


def test_comatibility_of_old_product_based_travel_method() -> None:
    """The transition helper delegates through the product's planet."""
    model = get_ship_model("standard_s_1")

    assert model.calculate_travel_rounds(Product.GEMS) == (
        model.calculate_travel_rounds_to(Product.GEMS.planet)
    )
