"""Permanent business investments and the player's investment portfolio."""

from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Final

from galactic_trader.exceptions import (
    InvestmentAlreadyOwnedException,
    UnknownInvestmentException,
)


@unique
class InvestmentModifier(Enum):
    """Identify game values that an investment can modify."""

    PRODUCTION_COST = "Production cost"
    SHIP_PURCHASE_PRICE = "Spaceship purchase price"

    def __str__(self) -> str:
        """Return the player-friendly modifier name."""
        return self.value


@dataclass(frozen=True)
class InvestmentEffect:
    """Describe one permanent multiplier applied to a game value."""

    modifier: InvestmentModifier
    multiplier: float

    def __post_init__(self) -> None:
        """Validate the modifier and its positive multiplier."""
        if not isinstance(self.modifier, InvestmentModifier):
            raise TypeError("Modifier must be an instance of InvestmentModifier.")
        if not 0 < self.multiplier <= 1:
            raise ValueError(
                "Investment multiplier must be greater than zero and at most one."
            )


@dataclass(frozen=True)
class InvestmentInfo:
    """Describe one purchasable permanent business investment."""

    display_name: str
    description: str
    purchase_price: float
    effects: tuple[InvestmentEffect, ...]

    def __post_init__(self) -> None:
        """Validate the fixed investment information."""
        if not self.display_name.strip():
            raise ValueError("Investment display name must not be empty.")
        if not self.description.strip():
            raise ValueError("Investment description must not be empty.")
        if self.purchase_price <= 0:
            raise ValueError("Investment purchase price must be greater than zero.")
        if not self.effects:
            raise ValueError("An investment requires at least one effect.")
        if any(not isinstance(effect, InvestmentEffect) for effect in self.effects):
            raise TypeError("Investment effects must be InvestmentEffect instances.")

        modifiers = tuple(effect.modifier for effect in self.effects)
        if len(set(modifiers)) != len(modifiers):
            raise ValueError(
                "An investment cannot modify the same value more than once."
            )


@unique
class Investment(Enum):
    """Contain all permanent business investments."""

    FACTORY = InvestmentInfo(
        display_name="Factory",
        description="Reduces all production costs by 25%.",
        purchase_price=2500.0,
        effects=(
            InvestmentEffect(
                modifier=InvestmentModifier.PRODUCTION_COST,
                multiplier=0.75,
            ),
        ),
    )
    SHIPYARD = InvestmentInfo(
        display_name="Shipyard",
        description="Reduces all spaceship purchase prices by 15%.",
        purchase_price=3500.0,
        effects=(
            InvestmentEffect(
                modifier=InvestmentModifier.SHIP_PURCHASE_PRICE,
                multiplier=0.85,
            ),
        ),
    )

    @property
    def investment_id(self) -> str:
        """Return the stable identifier used by terminal commands."""
        return self.name.lower()

    @property
    def display_name(self) -> str:
        """Return the user-facing investment name."""
        return self.value.display_name

    @property
    def description(self) -> str:
        """Return the user-facing investment description."""
        return self.value.description

    @property
    def purchase_price(self) -> float:
        """Return the base investment purchase price."""
        return self.value.purchase_price

    @property
    def effects(self) -> tuple[InvestmentEffect, ...]:
        """Return all permanent effects of this investment."""
        return self.value.effects

    def __str__(self) -> str:
        """Return the player-friendly investment name."""
        return self.display_name


ALL_INVESTMENTS: Final[tuple[Investment, ...]] = tuple(Investment)


def get_investment(investment_id: str) -> Investment:
    """Return the investment with the requested identifier."""
    normalized_id = investment_id.strip().upper()
    try:
        return Investment[normalized_id]
    except KeyError:
        available_ids = ", ".join(investment.investment_id for investment in Investment)
        raise UnknownInvestmentException(
            f"Unknown investment '{investment_id}'. "
            f"Available investment IDs: {available_ids}."
        ) from None


@dataclass
class InvestmentPortfolio:
    """Manage all permanent investments purchased by the player."""

    _owned: set[Investment] = field(
        default_factory=set,
        init=False,
        repr=False,
    )

    @property
    def owned(self) -> frozenset[Investment]:
        """Return an immutable view of all purchased investments."""
        return frozenset(self._owned)

    def owns(self, investment: Investment) -> bool:
        """Return whether an investment has already been purchased."""
        return investment in self._owned

    def add(self, investment: Investment) -> None:
        """Add an investment that has not previously been purchased."""
        if self.owns(investment):
            raise InvestmentAlreadyOwnedException(
                f"{investment} has already been purchased."
            )
        self._owned.add(investment)

    def get_multiplier(self, modifier: InvestmentModifier) -> float:
        """Return the combined multiplier for a game value."""
        multiplier = 1.0
        for investment in self._owned:
            for effect in investment.effects:
                if effect.modifier is modifier:
                    multiplier *= effect.multiplier
        return multiplier

    def __len__(self) -> int:
        """Return the number of purchased investments."""
        return len(self._owned)
