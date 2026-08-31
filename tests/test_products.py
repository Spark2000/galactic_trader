"""Tests for product definitions and starting-value validation."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.planets import Planet
from galactic_trader.products import Product, ProductInfo


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "exception_type"),
    [
        ("display_name", "", ValueError),
        ("starting_price", 0.5, ValueError),
        ("starting_volatility", -1.0, ValueError),
        ("cargo_type", "standard", TypeError),
        ("planet", "Endor", TypeError),
    ],
)
def test_product_info_rejects_invalid_values(
    field_name: str,
    invalid_value: object,
    exception_type: type[Exception],
) -> None:
    values: dict[str, object] = {
        "display_name": "Test Product",
        "starting_price": 10.0,
        "starting_volatility": 0.5,
        "cargo_type": CargoType.STANDARD,
        "planet": Planet.ENDOR,
    }
    values[field_name] = invalid_value

    with pytest.raises(exception_type):
        ProductInfo(**values)  # type: ignore[arg-type]


def test_product_exposes_its_information() -> None:
    assert Product.FOOD.display_name == Product.FOOD.value.display_name
    assert Product.FOOD.starting_price == Product.FOOD.value.starting_price
    assert Product.FOOD.starting_volatility == Product.FOOD.value.starting_volatility
    assert Product.FOOD.distance == Product.FOOD.value.planet.distance


def test_product_string_uses_display_name() -> None:
    assert str(Product.FURNITURE) == Product.FURNITURE.display_name


def test_every_product_has_exactly_one_planet() -> None:
    """Every product references one member of the Planet enum."""
    for product in Product:
        assert isinstance(product.planet, Planet)


def test_related_products_can_share_an_origin_planet() -> None:
    """Products from the same economy may reference the same planet."""
    assert Product.FOOD.planet is Planet.ALDERAAN
    assert Product.WOOD.planet is Planet.ENDOR
    assert Product.ORE.planet is Planet.KESSEL
    assert Product.METAL.planet is Planet.KESSEL


def test_product_distance_is_forwarded_from_planet() -> None:
    """The compatibility property always reflects the planet distance."""
    for product in Product:
        assert product.distance == product.planet.distance
