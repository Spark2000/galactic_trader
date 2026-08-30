"""Defines random market events and apply their price effects."""

from dataclasses import dataclass
from random import Random
from typing import Final

from galactic_trader.market import Market
from galactic_trader.products import Product

DEFAULT_EVENT_PROBABILITY: Final[float] = 0.20
MAX_EVENT_PERCENTAGE: Final[float] = 0.20


@dataclass(frozen=True)
class MarketEvent:
    """Defines an event."""

    name: str
    description: str
    affected_products: tuple[Product, ...]
    # tuple is better for testing than set because it has an order
    direction: int
    min_percentage: float
    max_percentage: float

    def __post_init__(self) -> None:
        """Validates the event definition."""
        if not self.name.strip():
            raise ValueError("An event requires a name.")
        if not self.description.strip():
            raise ValueError("An event requires a description.")
        if not self.affected_products:
            raise ValueError("An event must affect at least one product.")
        if len(set(self.affected_products)) != len(self.affected_products):
            raise ValueError("Affected products must not contain duplicates.")
        if self.direction not in {-1, 1}:
            raise ValueError("Event direction must be either -1 or 1.")
        if not (0 < self.min_percentage <= self.max_percentage <= MAX_EVENT_PERCENTAGE):
            raise ValueError(
                "Event percentages must satisfy "
                f"0 < min <= max <= {MAX_EVENT_PERCENTAGE:.0%}."
            )

    def apply(
        self, markets: dict[Product, Market], random_gen: Random
    ) -> EventOccurrence:
        percentage = random_gen.uniform(self.min_percentage, self.max_percentage)
        signed_percentage = self.direction * percentage

        for product in self.affected_products:
            market = markets[product]
            market.set_price(market.current_price * (1 + signed_percentage))

        return EventOccurrence(event=self, percentage_change=signed_percentage)


@dataclass(frozen=True)
class EventOccurrence:
    """Describe one market event that occurred in a round."""

    event: MarketEvent
    percentage_change: float

    @property
    def message(self) -> str:
        """Return a user-fiendly description of the event."""
        products = ", ".join(str(product) for product in self.event.affected_products)
        direction = "increased" if self.percentage_change > 0 else "decreased"

        return (
            f"{self.event.name}: {self.event.description} "
            f"The price of {products} {direction} by "
            f"{abs(self.percentage_change):.1%}."
        )


ALL_PRODUCTS: Final[tuple[Product, ...]] = tuple(Product)

MARKET_EVENTS: Final[tuple[MarketEvent, ...]] = (
    MarketEvent(
        name="Drought",
        description="Poor harvests reduce the food supply.",
        affected_products=(Product.FOOD,),
        direction=1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="Record harvest",
        description="An excellent harvest increases the food supply.",
        affected_products=(Product.FOOD,),
        direction=-1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="Mine collapse",
        description="Ore production is temporarily disrupted.",
        affected_products=(Product.ORE,),
        direction=1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="New ore vein discovery",
        description="A new deposit increases the ore supply.",
        affected_products=(Product.ORE,),
        direction=-1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="Forest fire",
        description="Destroyed forests make wood scarce.",
        affected_products=(Product.WOOD,),
        direction=1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="Forestry expansion",
        description="New plantations increase the wood supply.",
        affected_products=(Product.WOOD,),
        direction=-1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="Factory breakdown",
        description="Furniture production slows down.",
        affected_products=(Product.FURNITURE,),
        direction=1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="EKEA sale",
        description="The largest furniture store in the galaxy 'EKEA' offers large discounts.",
        affected_products=(Product.FURNITURE,),
        direction=-1,
        min_percentage=0.08,
        max_percentage=0.15,
    ),
    MarketEvent(
        name="War",
        description="Due to uncertainty, costs rise across the economy.",
        affected_products=ALL_PRODUCTS,
        direction=1,
        min_percentage=0.04,
        max_percentage=0.08,
    ),
    MarketEvent(
        name="Trade agreement",
        description="Lower trade barriers make goods cheaper.",
        affected_products=ALL_PRODUCTS,
        direction=-1,
        min_percentage=0.04,
        max_percentage=0.08,
    ),
)


def choose_market_event(
    random_generator: Random, event_probability: float = DEFAULT_EVENT_PROBABILITY
) -> MarketEvent | None:
    """Randomly select an event or return ``None`` if not event occures in this round."""
    if not 0 <= event_probability <= 1:
        raise ValueError("Event probability must be between zero and one.")

    if event_probability == 0:
        return None
    if event_probability < 1 and random_generator.random() >= event_probability:
        return None

    return random_generator.choice(MARKET_EVENTS)
