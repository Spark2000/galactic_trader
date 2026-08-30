"""Tests for product definitions and starting-value validation."""

import pytest

from galactic_trader.products import Product, ProductInfo


def test_initial_current_price_value_too_low() -> None:
    with pytest.raises(ValueError):
        ProductInfo(display_name="Food", starting_price=0.5, starting_volatility=0.5)


def test_initial_volatility_value_too_low() -> None:
    with pytest.raises(ValueError):
        ProductInfo(display_name="Food", starting_price=10.0, starting_volatility=-1)


def test_empty_display_name_is_rejected() -> None:
    with pytest.raises(ValueError):
        ProductInfo(display_name=" ", starting_price=10.0, starting_volatility=0.5)


def test_product_exposes_its_information() -> None:
    assert Product.FOOD.display_name == Product.FOOD.value.display_name
    assert Product.FOOD.starting_price == Product.FOOD.value.starting_price
    assert Product.FOOD.starting_volatility == Product.FOOD.value.starting_volatility


def test_product_string_uses_display_name() -> None:
    assert str(Product.FURNITURE) == Product.display_name
