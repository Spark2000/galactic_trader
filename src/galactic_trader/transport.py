"""Data objects used by product transport and round completion."""

from dataclasses import dataclass

from galactic_trader.products import Product


@dataclass(frozen=True)
class TransportOption:
    """Describes one available spaceship for a planned purchase."""

    ship_id: int
    ship_name: str
    cargo_capacity: int
    travel_rounds: int


@dataclass
class TransportMission:
    """Represents an active mission collecting purchased products."""

    product: Product
    quantity: int
    total_rounds: int
    remaining_rounds: int

    def __post_init__(self) -> None:
        """Validate the initial mission state."""
        if self.quantity <= 0:
            raise ValueError("Transport quantity must be greater than 0.")
        if self.total_rounds <= 0:
            raise ValueError("Total travel rounds must be greater than 0.")
        if not 0 < self.remaining_rounds <= self.total_rounds:
            raise ValueError(
                "Remaining rounds must be between 1 and total rounds."
            )

    def advance(self) -> bool:
        """Advance the mission and return whether it has been completed."""
        if self.remaining_rounds <= 0:
            raise RuntimeError("A completed transport cannot advance again.")

        self.remaining_rounds -= 1
        return self.remaining_rounds == 0


@dataclass(frozen=True)
class ProductPurchase:
    """Describe a completed purchase and its newly started transport."""

    product: Product
    quantity: int
    ship_id: int
    ship_name: str
    unit_price: float
    total_cost: float
    travel_rounds: int


@dataclass(frozen=True)
class CompletedDelivery:
    """Describe products delivered by one spaceship during a tick."""

    ship_id: int
    ship_name: str
    product: Product
    quantity: int

    @property
    def message(self) -> str:
        """Return a player-friendly delivery message."""
        return (
            f"{self.quantity} {self.product} arrived with "
            f"{self.ship_name} (ID: #{self.ship_id})."
        )
