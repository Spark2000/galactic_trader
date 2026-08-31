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
        """Apply this event to its markets and return the occurrence."""
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
        name="Asteroid mine collapse",
        description="Ore extraction and metal production are disrupted.",
        affected_products=(Product.ORE, Product.METAL),
        direction=1,
        min_percentage=0.07,
        max_percentage=0.13,
    ),
    MarketEvent(
        name="Rich asteroid field",
        description="Scouts habe discovered unusually accessible ore deposits.",
        affected_products=(Product.ORE, Product.METAL),
        direction=-1,
        min_percentage=0.07,
        max_percentage=0.13,
    ),
    MarketEvent(
        name="Forest fire",
        description="Destroyed forests interrupt logging.",
        affected_products=(Product.WOOD, Product.FURNITURE),
        direction=1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Forestry expansion",
        description="New orbital greenhouses increase the wood supply.",
        affected_products=(Product.WOOD, Product.FURNITURE),
        direction=-1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Factory breakdown",
        description="Furniture production slows down across the sector.",
        affected_products=(Product.FURNITURE,),
        direction=1,
        min_percentage=0.08,
        max_percentage=0.14,
    ),
    MarketEvent(
        name="EKEA sale",
        description="EKEA offers discounts after finding a warehouse moon.",
        affected_products=(Product.FURNITURE,),
        direction=-1,
        min_percentage=0.08,
        max_percentage=0.14,
    ),
    MarketEvent(
        name="Oil rig accident",
        description="A drilling station is closed for emergency repairs.",
        affected_products=(Product.OIL, Product.FUEL),
        direction=1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Titan refinery boom",
        description="New refineries flood nearby systems with oil products.",
        affected_products=(Product.OIL, Product.FUEL),
        direction=-1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Space flu outbreak",
        description="Demand for medicine rises throughout the colonies.",
        affected_products=(Product.MEDICINE,),
        direction=1,
        min_percentage=0.10,
        max_percentage=0.18,
    ),
    MarketEvent(
        name="Universal vaccine",
        description="A new vaccine reduces emergency medical demand.",
        affected_products=(Product.MEDICINE,),
        direction=-1,
        min_percentage=0.10,
        max_percentage=0.18,
    ),
    MarketEvent(
        name="Intergalactic fashion week",
        description="The latest zero-gravity styles become essential.",
        affected_products=(Product.TEXTILES, Product.CLOTHING),
        direction=1,
        min_percentage=0.07,
        max_percentage=0.13,
    ),
    MarketEvent(
        name="Last season's spacesuits",
        description="Retailers discount yesterday's supposedly timeless look.",
        affected_products=(Product.TEXTILES, Product.CLOTHING),
        direction=-1,
        min_percentage=0.07,
        max_percentage=0.13,
    ),
    MarketEvent(
        name="Robot union strike",
        description="Automated workers demand scheduled charging breaks.",
        affected_products=(Product.MACHINES, Product.ELECTRONICS, Product.ROBOTS),
        direction=1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Turn it off and on again",
        description="A legendary technician fixes the automation network.",
        affected_products=(Product.MACHINES, Product.ELECTRONICS, Product.ROBOTS),
        direction=-1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Galactic arms race",
        description="Several systems rapidly expand their arsenals.",
        affected_products=(Product.WEAPONS,),
        direction=1,
        min_percentage=0.10,
        max_percentage=0.18,
    ),
    MarketEvent(
        name="Peace dividend",
        description="Disarmament releases surplus weapons onto the market.",
        affected_products=(Product.WEAPONS,),
        direction=-1,
        min_percentage=0.10,
        max_percentage=0.18,
    ),
    MarketEvent(
        name="Pirate blockade",
        description="Raiders interrupt deliveries of essential supplies.",
        affected_products=(Product.FOOD, Product.FUEL, Product.MEDICINE),
        direction=1,
        min_percentage=0.05,
        max_percentage=0.10,
    ),
    MarketEvent(
        name="Ranger patrols",
        description="Secure trade lanes restore the supply of essentials.",
        affected_products=(Product.FOOD, Product.FUEL, Product.MEDICINE),
        direction=-1,
        min_percentage=0.05,
        max_percentage=0.10,
    ),
    MarketEvent(
        name="Quantum chip shortage",
        description="Advanced production waits for missing control chips.",
        affected_products=(Product.ELECTRONICS, Product.ROBOTS, Product.STARSHIP_PARTS),
        direction=1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Open-source circuit breakthrough",
        description="Free circuit designs simplify advanced manufacturing.",
        affected_products=(Product.ELECTRONICS, Product.ROBOTS, Product.STARSHIP_PARTS),
        direction=-1,
        min_percentage=0.06,
        max_percentage=0.12,
    ),
    MarketEvent(
        name="Royal asteroid wedding",
        description="Half the galaxy suddenly wants gem-studded rings.",
        affected_products=(Product.GEMS, Product.JEWELRY),
        direction=1,
        min_percentage=0.07,
        max_percentage=0.14,
    ),
    MarketEvent(
        name="Rocks are so last millennium",
        description="An influencer declares natural gems unfashionable.",
        affected_products=(Product.GEMS, Product.JEWELRY),
        direction=-1,
        min_percentage=0.07,
        max_percentage=0.14,
    ),
    MarketEvent(
        name="War",
        description="Uncertainty and military demand raise prices everywhere.",
        affected_products=ALL_PRODUCTS,
        direction=1,
        min_percentage=0.03,
        max_percentage=0.06,
    ),
    MarketEvent(
        name="Trade agreement",
        description="Lower trade barriers make goods cheaper everywhere.",
        affected_products=ALL_PRODUCTS,
        direction=-1,
        min_percentage=0.03,
        max_percentage=0.06,
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
