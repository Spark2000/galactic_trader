"""Player-owned spaceship instances and fleet management."""

from dataclasses import dataclass, field

from galactic_trader.exceptions import ShipNotOwnedException
from galactic_trader.ships import ShipModel


@dataclass(frozen=True)
class OwnedShip:
    """Represents one concrete spaceship owned by the player."""

    ship_id: int
    model: ShipModel

    def __post_init__(self) -> None:
        """Validate the player-specific spaceship ID."""
        if self.ship_id <= 0:
            raise ValueError("Ship ID must be greater than zero.")

    def __str__(self) -> str:
        """Return the owned ship's ID and model name."""
        return f"{self.model.display_name} (ID: #{self.ship_id})"


@dataclass
class Fleet:
    """Manages all individual spaceships owned by the player."""

    _ships: list[OwnedShip] = field(default_factory=list, init=False, repr=False)
    _next_ship_id: int = field(default=1, init=False, repr=False)

    @property
    def ships(self) -> tuple[OwnedShip, ...]:
        """Return all owned ships without exposing the mutable internal list."""
        return tuple(self._ships)

    def add_ship(self, model: ShipModel) -> OwnedShip:
        """Create and store one independently identifiable spaceship."""
        owned_ship = OwnedShip(
            ship_id=self._next_ship_id,
            model=model,
        )
        self._ships.append(owned_ship)
        self._next_ship_id += 1
        return owned_ship

    def get_ship(self, ship_id: int) -> OwnedShip:
        """Return the owned spaceship with the requested ID."""
        for owned_ship in self._ships:
            if owned_ship.ship_id == ship_id:
                return owned_ship

        raise ShipNotOwnedException(
            f"No owned spaceship has the ID {ship_id}."
        )

    def remove_ship(self, ship_id: int) -> OwnedShip:
        """Remove and return exactly one owned spaceship."""
        owned_ship = self.get_ship(ship_id)
        self._ships.remove(owned_ship)
        return owned_ship

    def __len__(self) -> int:
        """Return the number of owned spaceships."""
        return len(self._ships)
