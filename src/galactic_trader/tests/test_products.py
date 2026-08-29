import pytest

from galactic_trader.products import *


def test_initial_current_price_value_too_low() -> None:
    with pytest.raises(ValueError):
        ProductInfo(display_name="Food", starting_price=0.5, starting_volatility=0.5)


def test_initial_volatility_value_too_low() -> None:
    with pytest.raises(ValueError):
        ProductInfo(display_name="Food", starting_price=10.0, starting_volatility=-1)
