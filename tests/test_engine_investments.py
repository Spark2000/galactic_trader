"""Integration tests for purchasing and applying investments."""

import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.exceptions import (
    InvestmentAlreadyOwnedException,
    NotEnoughMoneyException,
)
from galactic_trader.investments import Investment
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model


@pytest.fixture
def engine() -> EconomyEngine:
    """Return a deterministic engine with enough money for investments."""
    result = EconomyEngine(
        random_seed=1,
        event_probability=0,
        pirate_attack_probability=0,
    )
    result.player.money = 10000.0
    return result


def test_buy_investment_deducts_money_and_records_purchase(
    engine: EconomyEngine,
) -> None:
    """A successful purchase updates money, ownership, and history."""
    investment, price = engine.buy_investment(Investment.FACTORY)

    assert investment is Investment.FACTORY
    assert price == pytest.approx(2500.0)
    assert engine.player.money == pytest.approx(7500)
    assert engine.investments.owns(Investment.FACTORY)
    assert engine.history[-1] == (
        "BUY_INVESTMENT",
        "Factory",
        1,
        2500.0,
    )


def test_investment_cannot_be_bought_twice(
    engine: EconomyEngine,
) -> None:
    """A failed duplicate purchase leaves money and ownership unchanged."""
    engine.buy_investment(Investment.FACTORY)
    money_after_first_purchase = engine.player.money

    with pytest.raises(InvestmentAlreadyOwnedException):
        engine.buy_investment(Investment.FACTORY)

    assert engine.player.money == money_after_first_purchase
    assert engine.investments.owned == frozenset({Investment.FACTORY})


def test_unaffordable_investment_is_not_added() -> None:
    """Insufficient credits do not activate an investment."""
    engine = EconomyEngine(
        event_probability=0,
        pirate_attack_probability=0,
    )

    with pytest.raises(NotEnoughMoneyException):
        engine.buy_investment(Investment.FACTORY)

    assert not engine.investments.owns(Investment.FACTORY)
    assert engine.player.money == pytest.approx(100.0)


def test_factory_reduces_cost_but_not_materials(
    engine: EconomyEngine,
) -> None:
    """Factory ownership discounts credits while consuming full materials."""
    quantity = 2
    recipe = PRODUCTION_RECIPES[Product.METAL]
    required_ore = recipe.materials[Product.ORE] * quantity
    engine.player.stock[Product.ORE] = required_ore
    engine.buy_investment(Investment.FACTORY)
    money_before_production = engine.player.money

    action, total_cost = engine.produce_product(Product.METAL, quantity)

    assert action == "PRODUCE"
    assert total_cost == pytest.approx(recipe.calculate_total_cost(quantity) * 0.75)
    assert engine.player.money == pytest.approx(money_before_production - total_cost)
    assert engine.player.stock[Product.ORE] == 0
    assert engine.player.stock[Product.METAL] == quantity


def test_shipyard_reduces_displayed_and_paid_ship_price(
    engine: EconomyEngine,
) -> None:
    """Shipyard ownership applies the same price to display and purchase."""
    model = get_ship_model("standard_l_1")
    engine.buy_investment(Investment.SHIPYARD)
    expected_price = round(model.purchase_price * 0.85, 2)
    money_before_ship = engine.player.money

    assert engine.get_ship_purchase_price(model) == expected_price

    owned_ship, paid_price = engine.buy_ship(model.model_id)

    assert owned_ship.model is model
    assert paid_price == expected_price
    assert engine.player.money == pytest.approx(money_before_ship - expected_price)


def test_investment_effects_do_not_affect_unrelated_prices(
    engine: EconomyEngine,
) -> None:
    """Factory and Shipyard modify only their respective price category."""
    model = get_ship_model("standard_s_1")
    base_production_cost = engine.get_production_cost(Product.METAL)

    engine.buy_investment(Investment.FACTORY)

    assert engine.get_ship_purchase_price(model) == model.purchase_price
    factory_production_cost = engine.get_production_cost(Product.METAL)
    assert factory_production_cost == pytest.approx(base_production_cost * 0.75)

    engine.buy_investment(Investment.SHIPYARD)

    assert engine.get_production_cost(Product.METAL) == (factory_production_cost)
    assert engine.get_ship_purchase_price(model) == pytest.approx(
        model.purchase_price * 0.85
    )


def test_shipyard_does_not_reduce_ship_resale_value(
    engine: EconomyEngine,
) -> None:
    """Ship resale remains based on the unchanged catalog price."""
    model = get_ship_model("standard_s_1")
    engine.buy_investment(Investment.SHIPYARD)
    owned_ship, paid_price = engine.buy_ship(model.model_id)

    sold_ship, sale_price = engine.sell_ship(owned_ship.ship_id)

    assert sold_ship is owned_ship
    assert paid_price == pytest.approx(model.purchase_price * 0.85)
    assert sale_price == pytest.approx(model.purchase_price * 0.70)
