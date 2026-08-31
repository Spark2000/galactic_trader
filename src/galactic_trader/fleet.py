"""Player-owned spaceship instances and fleet management."""

from dataclasses import dataclass, field

from galactic_trader.exceptions import ShipInTransitException, ShipNotOwnedException
from galactic_trader.products import Product
from galactic_trader.ships import ShipModel
from galactic_trader.transport import TransportMission


@dataclass
class OwnedShip:
    """Represents one concrete spaceship owned by the player."""

    ship_id: int
    model: ShipModel
    active_transport: TransportMission | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Validate the player-specific spaceship ID."""
        if self.ship_id <= 0:
            raise ValueError("Ship ID must be greater than zero.")

    @property
    def is_available(self) -> bool:
        """Return whether this ship can start a new transport."""
        return self.active_transport is None

    def start_transport(self, mission: TransportMission) -> None:
        """Assign a new transport to this ship."""
        if not self.is_available:
            raise ShipInTransitException(f"{self} is already in transit.")
        self.active_transport = mission

    def advance_transport(self) -> TransportMission | None:
        """Advance the active transport and return it when completed."""
        if self.active_transport is None:
            return None
        if not self.active_transport.advance():
            return None

        completed_transport = self.active_transport
        self.active_transport = None
        return completed_transport

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
        """Returns all owned ships without exposing the mutable internal list."""
        return tuple(self._ships)

    def add_ship(self, model: ShipModel) -> OwnedShip:
        """Creates and store one independently identifiable spaceship."""
        owned_ship = OwnedShip(
            ship_id=self._next_ship_id,
            model=model,
        )
        self._ships.append(owned_ship)
        self._next_ship_id += 1
        return owned_ship

    def get_ship(self, ship_id: int) -> OwnedShip:
        """Returns the owned spaceship with the requested ID."""
        for owned_ship in self._ships:
            if owned_ship.ship_id == ship_id:
                return owned_ship

        raise ShipNotOwnedException(f"No owned spaceship has the ID {ship_id}.")

    def get_available_ships(
        self, product: Product, quantity: int
    ) -> tuple[OwnedShip, ...]:
        """Returns free ships with a compatible and sufficiently large hold."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        return tuple(
            ship
            for ship in self._ships
            if ship.is_available
            and ship.model.can_transport(product)
            and ship.model.cargo_capacity >= quantity
        )

    def remove_ship(self, ship_id: int) -> OwnedShip:
        """Remove and return exactly one available spaceship."""
        owned_ship = self.get_ship(ship_id)
        if not owned_ship.is_available:
            raise ShipInTransitException(
                f"{owned_ship} cannot be sold while it is in transit."
            )

        self._ships.remove(owned_ship)
        return owned_ship

    def __len__(self) -> int:
        """Return the number of owned spaceships."""
        return len(self._ships)
