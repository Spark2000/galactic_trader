"""UI-facing controller for the pygame-ce interface."""

from pathlib import Path

from galactic_trader.engine import EconomyEngine, RoundResult
from galactic_trader.fleet import OwnedShip
from galactic_trader.investments import Investment
from galactic_trader.products import Product
from galactic_trader.savegame import (
    DEFAULT_SAVE_DIRECTORY,
    list_save_games,
    load_game,
    save_game,
)
from galactic_trader.ships import ShipModel
from galactic_trader.transport import ProductPurchase, TransportOption


class GameController:
    """Expose engine operations in a form convenient for a graphical UI."""

    def __init__(
        self,
        engine: EconomyEngine,
        *,
        save_directory: Path = DEFAULT_SAVE_DIRECTORY,
    ) -> None:
        """Store the active engine and the directory used for save games."""
        self.engine = engine
        self.save_directory = Path(save_directory)

    def transport_options(
        self,
        product: Product,
        quantity: int,
    ) -> tuple[TransportOption, ...]:
        """Return every ship that can collect the requested purchase."""
        return self.engine.get_transport_options(product, quantity)

    def buy_product(
        self,
        product: Product,
        quantity: int,
        ship_id: int,
    ) -> ProductPurchase:
        """Buy a product and start its transport mission."""
        return self.engine.buy_product(product, quantity, ship_id)

    def sell_product(self, product: Product, quantity: int) -> tuple[str, float]:
        """Sell stocked goods immediately."""
        return self.engine.sell_product(product, quantity)

    def produce_product(self, product: Product, quantity: int) -> tuple[str, float]:
        """Produce a quantity of a product from its recipe."""
        return self.engine.produce_product(product, quantity)

    def buy_ship(self, model: ShipModel) -> tuple[OwnedShip, float]:
        """Buy one ship of the supplied model."""
        return self.engine.buy_ship(model.model_id)

    def sell_ship(self, ship_id: int) -> tuple[OwnedShip, float]:
        """Sell one available owned ship."""
        return self.engine.sell_ship(ship_id)

    def buy_investment(
        self,
        investment: Investment,
    ) -> tuple[Investment, float]:
        """Buy one permanent investment."""
        return self.engine.buy_investment(investment)

    def advance_round(self) -> RoundResult:
        """Advance the simulation by one round."""
        return self.engine.tick()

    def save(self) -> Path:
        """Write the current engine state to a timestamped save game."""
        return save_game(self.engine, self.save_directory)

    def available_saves(self) -> tuple[Path, ...]:
        """Return all available save game files."""
        return tuple(list_save_games(self.save_directory))

    def load(self, save_name: str) -> EconomyEngine:
        """Load and activate one save game."""
        self.engine = load_game(save_name, self.save_directory)
        return self.engine
