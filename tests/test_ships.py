"""Tests for spaceship model definitions and balancing."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.products import Product
from galactic_trader.ships import ShipModel, get_all_ship_models, get_ship_models


def test_model_names_are_unique() -> None:
    models = get_all_ship_models()
    names = [model.display_name for model in models]

    assert len(models) >= 13
    assert len(names) == len(set(names))


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
