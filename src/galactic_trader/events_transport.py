"""Resolve random events that affect active product transports."""

from dataclasses import dataclass
from math import ceil
from random import Random
from typing import Final

from galactic_trader.fleet import Fleet
from galactic_trader.products import Product

DEFAULT_PIRATE_ATTACK_PROBABILITY: Final[float] = 0.05
MIN_STOLEN_PERCENTAGE: Final[int] = 30
MAX_STOLEN_PERCENTAGE: Final[int] = 100


@dataclass(frozen=True)
class PirateAttackOccurrence:
    """Describes the outcome of one pirate attack."""

    ship_id: int
    ship_name: str
    product: Product
    defended: bool
    stolen_quantity: int
    remaining_quantity: int
    loss_percentage: int | None

    def __post_init__(self) -> None:
        """Validates the immutable attack result."""
        if self.ship_id <= 0:
            raise ValueError("Ship ID must be greater than zero.")
        if not self.ship_name.strip():
            raise ValueError("Ship name must not be empty.")
        if self.stolen_quantity < 0:
            raise ValueError("Stolen quantity must not be negative.")
        if self.remaining_quantity < 0:
            raise ValueError("Remaining quantity must not be negative.")

        if self.defended:
            if self.stolen_quantity != 0 or self.loss_percentage is not None:
                raise ValueError("A defended attack cannot contain a cargo loss.")
        elif not (
            MIN_STOLEN_PERCENTAGE
            <= (self.loss_percentage or 0)
            <= MAX_STOLEN_PERCENTAGE
        ):
            raise ValueError("A successful attack requires a valid loss percentage.")

    @property
    def message(self) -> str:
        """Returns a player-friendly description of the pirate attack."""
        ship_display = f"{self.ship_name} (ID: #{self.ship_id})"
        if self.defended:
            return f"{ship_display} repelled a pirate attack. No cargo was lost."
        if self.remaining_quantity == 0:
            return (
                f"Pirates attacked {ship_display} and stole all "
                f"{self.stolen_quantity} {self.product}."
            )
        return (
            f"Pirates attacked {ship_display} and stole "
            f"{self.stolen_quantity} {self.product}. "
            f"{self.remaining_quantity} remain."
        )


def resolve_pirate_attack(
    fleet: Fleet,
    random_generator: Random,
    probability: float,
) -> PirateAttackOccurrence | None:
    """Possibly attack one randomly selected cargo-bearing transport."""
    if not 0 <= probability <= 1:
        raise ValueError("Pirate attack probability must be between zero and one.")

    attackable_ships = tuple(
        ship
        for ship in fleet.ships
        if ship.active_transport is not None and ship.active_transport.quantity > 0
    )
    if not attackable_ships:
        return None
    if random_generator.random() >= probability:
        return None

    attacked_ship = random_generator.choice(attackable_ships)
    mission = attacked_ship.active_transport
    if mission is None:
        raise RuntimeError("Selected pirate target has no transport mission.")

    defense_probability = attacked_ship.model.defense_rating / 100
    if random_generator.random() < defense_probability:
        return PirateAttackOccurrence(
            ship_id=attacked_ship.ship_id,
            ship_name=attacked_ship.model.display_name,
            product=mission.product,
            defended=True,
            stolen_quantity=0,
            remaining_quantity=mission.quantity,
            loss_percentage=None,
        )

    loss_percentage = random_generator.randint(
        MIN_STOLEN_PERCENTAGE,
        MAX_STOLEN_PERCENTAGE,
    )
    requested_loss = ceil(mission.quantity * loss_percentage / 100)
    stolen_quantity = mission.remove_cargo(requested_loss)

    return PirateAttackOccurrence(
        ship_id=attacked_ship.ship_id,
        ship_name=attacked_ship.model.display_name,
        product=mission.product,
        defended=False,
        stolen_quantity=stolen_quantity,
        remaining_quantity=mission.quantity,
        loss_percentage=loss_percentage,
    )
