"""Tests for product definitions and starting-value validation."""

import pytest

from galactic_trader.cargo import CargoType
from galactic_trader.products import Product, ProductInfo


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "exception_type"),
    [
        ("display_name", "", ValueError),
        ("starting_price", 0.5, ValueError),
        ("starting_volatility", -1.0, ValueError),
        ("cargo_type", "standard", TypeError),
        ("distance", 0, ValueError),
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
        "distance": 40,
    }
    values[field_name] = invalid_value

    with pytest.raises(exception_type):
        ProductInfo(**values)  # type: ignore[arg-type]


def test_product_exposes_its_information() -> None:
    assert Product.FOOD.display_name == Product.FOOD.value.display_name
    assert Product.FOOD.starting_price == Product.FOOD.value.starting_price
    assert Product.FOOD.starting_volatility == Product.FOOD.value.starting_volatility
    assert Product.FOOD.distance == Product.FOOD.value.distance


def test_product_string_uses_display_name() -> None:
    assert str(Product.FURNITURE) == Product.FURNITURE.display_name

def test_every_product_has_a_positive_distance() -> None:
    assert all(product.distance > 0 for product in Product)