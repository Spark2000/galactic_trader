"""Unit tests for investment definitions and portfolio state."""

import pytest

from galactic_trader.exceptions import InvestmentAlreadyOwnedException
from galactic_trader.investments import (
    Investment,
    InvestmentEffect,
    InvestmentModifier,
    InvestmentPortfolio,
    get_investment,
)


def test_investment_names_and_identifiers() -> None:
    """Investments expose stable command IDs and requested display names."""
    assert Investment.FACTORY.investment_id == "factory"
    assert Investment.FACTORY.display_name == "Factory"
    assert Investment.SHIPYARD.investment_id == "shipyard"
    assert Investment.SHIPYARD.display_name == "Shipyard"


def test_get_investment_normalizes_identifier() -> None:
    """Investment lookup ignores surrounding spaces and letter case."""
    assert get_investment("  FACTORY ") is Investment.FACTORY
    assert get_investment("shipyard") is Investment.SHIPYARD


def test_portfolio_is_initially_empty_and_has_neutral_multipliers() -> None:
    """A new player starts without any permanent investment effects."""
    portfolio = InvestmentPortfolio()

    assert portfolio.owned == frozenset()
    assert len(portfolio) == 0
    assert portfolio.get_multiplier(InvestmentModifier.PRODUCTION_COST) == 1
    assert (
        portfolio.get_multiplier(
            InvestmentModifier.SHIP_PURCHASE_PRICE
        )
        == 1
    )


def test_portfolio_applies_only_matching_investment_effects() -> None:
    """Each purchased investment modifies only its configured game value."""
    portfolio = InvestmentPortfolio()

    portfolio.add(Investment.FACTORY)

    assert portfolio.owns(Investment.FACTORY)
    assert (
        portfolio.get_multiplier(InvestmentModifier.PRODUCTION_COST)
        == pytest.approx(0.75)
    )
    assert (
        portfolio.get_multiplier(
            InvestmentModifier.SHIP_PURCHASE_PRICE
        )
        == 1
    )

    portfolio.add(Investment.SHIPYARD)

    assert (
        portfolio.get_multiplier(
            InvestmentModifier.SHIP_PURCHASE_PRICE
        )
        == pytest.approx(0.85)
    )


def test_portfolio_rejects_duplicate_investment() -> None:
    """The same permanent investment cannot be added twice."""
    portfolio = InvestmentPortfolio()
    portfolio.add(Investment.FACTORY)

    with pytest.raises(InvestmentAlreadyOwnedException):
        portfolio.add(Investment.FACTORY)

    assert portfolio.owned == frozenset({Investment.FACTORY})


@pytest.mark.parametrize("multiplier", [0, -0.1, 1.1])
def test_investment_effect_rejects_invalid_multiplier(
    multiplier: float,
) -> None:
    """Cost effects accept only positive non-increasing multipliers."""
    with pytest.raises(ValueError, match="Investment multiplier"):
        InvestmentEffect(
            modifier=InvestmentModifier.PRODUCTION_COST,
            multiplier=multiplier,
        )
