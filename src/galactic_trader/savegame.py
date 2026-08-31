"""Serialize and restore Galactic Trader game state as versioned JSON."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, cast

from galactic_trader.engine import MARKET_TRENDS, EconomyEngine
from galactic_trader.exceptions import (
    InvalidSaveGameException,
    SaveGameException,
    SaveGameNotFoundException,
    UnknownInvestmentException,
    UnknownShipModelException,
    UnsupportedSaveVersionException,
)
from galactic_trader.fleet import Fleet
from galactic_trader.inventory import Inventory
from galactic_trader.investments import get_investment
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model
from galactic_trader.transport import TransportMission

SAVE_SCHEMA_VERSION: Final[int] = 1
DEFAULT_SAVE_DIRECTORY: Final[Path] = Path("saves")
SAVE_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_-]+")

HistoryEntry = tuple[str, str, int, float]


@dataclass(frozen=True)
class MarketSaveData:
    """Store the mutable state of one product market."""

    current_price: float
    volatility: float


@dataclass(frozen=True)
class TransportSaveData:
    """Store one active transport mission."""

    product_id: str
    quantity: int
    total_rounds: int
    remaining_rounds: int


@dataclass(frozen=True)
class ShipSaveData:
    """Store one owned ship and its optional mission."""

    ship_id: int
    model_id: str
    active_transport: TransportSaveData | None


@dataclass(frozen=True)
class SaveGameData:
    """Contain every mutable value required to continue a saved game."""

    schema_version: int
    saved_at: str
    round_number: int
    money: float
    stock: dict[str, int]
    markets: dict[str, MarketSaveData]
    pending_price_directions: dict[str, int]
    history: tuple[HistoryEntry, ...]
    ships: tuple[ShipSaveData, ...]
    next_ship_id: int
    investments: tuple[str, ...]
    market_trend_index: int
    last_trend_multiplier: float
    last_effective_market_trend: float
    event_probability: float
    pirate_attack_probability: float

    @classmethod
    def from_engine(
        cls,
        engine: EconomyEngine,
        *,
        saved_at: datetime,
    ) -> SaveGameData:
        """Create serializable save data from an engine without changing it."""
        ships: list[ShipSaveData] = []
        for ship in engine.fleet.ships:
            mission = ship.active_transport
            transport_data = (
                None
                if mission is None
                else TransportSaveData(
                    product_id=mission.product.name,
                    quantity=mission.quantity,
                    total_rounds=mission.total_rounds,
                    remaining_rounds=mission.remaining_rounds,
                )
            )
            ships.append(
                ShipSaveData(
                    ship_id=ship.ship_id,
                    model_id=ship.model.model_id,
                    active_transport=transport_data,
                )
            )

        return cls(
            schema_version=SAVE_SCHEMA_VERSION,
            saved_at=saved_at.isoformat(timespec="seconds"),
            round_number=engine.round_number,
            money=engine.player.money,
            stock={
                product.name: quantity
                for product, quantity in engine.player.stock.items()
            },
            markets={
                product.name: MarketSaveData(
                    current_price=market.current_price,
                    volatility=market.volatility,
                )
                for product, market in engine.markets.items()
            },
            pending_price_directions={
                product.name: direction
                for product, direction in engine.pending_price_directions.items()
            },
            history=tuple(engine.history),
            ships=tuple(ships),
            next_ship_id=engine.fleet.next_ship_id,
            investments=tuple(
                sorted(
                    investment.investment_id for investment in engine.investments.owned
                )
            ),
            market_trend_index=engine.market_trend_index,
            last_trend_multiplier=engine.last_trend_multiplier,
            last_effective_market_trend=engine.last_effective_market_trend,
            event_probability=engine.event_probability,
            pirate_attack_probability=engine.pirate_attack_probability,
        )

    def to_json_object(self) -> dict[str, object]:
        """Convert this dataclass to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "saved_at": self.saved_at,
            "round_number": self.round_number,
            "player": {
                "money": self.money,
                "stock": self.stock,
            },
            "markets": {
                product_id: {
                    "current_price": market.current_price,
                    "volatility": market.volatility,
                }
                for product_id, market in self.markets.items()
            },
            "pending_price_directions": self.pending_price_directions,
            "history": [list(entry) for entry in self.history],
            "fleet": {
                "next_ship_id": self.next_ship_id,
                "ships": [
                    {
                        "ship_id": ship.ship_id,
                        "model_id": ship.model_id,
                        "active_transport": (
                            None
                            if ship.active_transport is None
                            else {
                                "product_id": ship.active_transport.product_id,
                                "quantity": ship.active_transport.quantity,
                                "total_rounds": ship.active_transport.total_rounds,
                                "remaining_rounds": (
                                    ship.active_transport.remaining_rounds
                                ),
                            }
                        ),
                    }
                    for ship in self.ships
                ],
            },
            "investments": list(self.investments),
            "round_state": {
                "market_trend_index": self.market_trend_index,
                "last_trend_multiplier": self.last_trend_multiplier,
                "last_effective_market_trend": (self.last_effective_market_trend),
            },
            "settings": {
                "event_probability": self.event_probability,
                "pirate_attack_probability": self.pirate_attack_probability,
            },
        }

    @classmethod
    def from_json_object(cls, raw: object) -> SaveGameData:
        """Validate a decoded JSON value and construct save-game data."""
        root = _require_dict(raw, "save game")
        schema_version = _require_int(
            root.get("schema_version"),
            "schema_version",
            minimum=1,
        )
        if schema_version != SAVE_SCHEMA_VERSION:
            raise UnsupportedSaveVersionException(
                f"Save schema version {schema_version} is not supported; "
                f"expected version {SAVE_SCHEMA_VERSION}."
            )

        saved_at = _require_string(root.get("saved_at"), "saved_at")
        try:
            datetime.fromisoformat(saved_at)
        except ValueError:
            raise InvalidSaveGameException(
                "Field 'saved_at' must contain an ISO date and time."
            ) from None

        player = _require_dict(root.get("player"), "player")
        stock = _read_int_mapping(
            player.get("stock"),
            "player.stock",
            minimum=0,
        )

        markets_raw = _require_dict(root.get("markets"), "markets")
        markets: dict[str, MarketSaveData] = {}
        for product_id, market_raw in markets_raw.items():
            _get_product(product_id, "markets")
            market = _require_dict(market_raw, f"markets.{product_id}")
            markets[product_id] = MarketSaveData(
                current_price=_require_float(
                    market.get("current_price"),
                    f"markets.{product_id}.current_price",
                    minimum=1.0,
                ),
                volatility=_require_float(
                    market.get("volatility"),
                    f"markets.{product_id}.volatility",
                    minimum=0.0,
                ),
            )

        for product_id in stock:
            _get_product(product_id, "player.stock")

        pending_directions = _read_int_mapping(
            root.get("pending_price_directions"),
            "pending_price_directions",
        )
        for product_id in pending_directions:
            _get_product(product_id, "pending_price_directions")

        history_raw = _require_list(root.get("history"), "history")
        history = tuple(
            _read_history_entry(entry, index) for index, entry in enumerate(history_raw)
        )

        fleet = _require_dict(root.get("fleet"), "fleet")
        ships_raw = _require_list(fleet.get("ships"), "fleet.ships")
        ships = tuple(
            _read_ship(ship_raw, index) for index, ship_raw in enumerate(ships_raw)
        )
        ship_ids = tuple(ship.ship_id for ship in ships)
        if len(set(ship_ids)) != len(ship_ids):
            raise InvalidSaveGameException("Fleet contains duplicate ship IDs.")

        investments_raw = _require_list(
            root.get("investments"),
            "investments",
        )
        investments = tuple(
            _require_string(value, f"investments[{index}]")
            for index, value in enumerate(investments_raw)
        )
        if len(set(investments)) != len(investments):
            raise InvalidSaveGameException("Investments must not contain duplicates.")
        for investment_id in investments:
            try:
                get_investment(investment_id)
            except UnknownInvestmentException as error:
                raise InvalidSaveGameException(str(error)) from None

        round_state = _require_dict(root.get("round_state"), "round_state")
        settings = _require_dict(root.get("settings"), "settings")

        return cls(
            schema_version=schema_version,
            saved_at=saved_at,
            round_number=_require_int(
                root.get("round_number"),
                "round_number",
                minimum=1,
            ),
            money=_require_float(
                player.get("money"),
                "player.money",
                minimum=0.0,
            ),
            stock=stock,
            markets=markets,
            pending_price_directions=pending_directions,
            history=history,
            ships=ships,
            next_ship_id=_require_int(
                fleet.get("next_ship_id"),
                "fleet.next_ship_id",
                minimum=1,
            ),
            investments=investments,
            market_trend_index=_require_int(
                round_state.get("market_trend_index"),
                "round_state.market_trend_index",
                minimum=0,
                maximum=len(MARKET_TRENDS) - 1,
            ),
            last_trend_multiplier=_require_float(
                round_state.get("last_trend_multiplier"),
                "round_state.last_trend_multiplier",
                minimum=0.0,
                minimum_exclusive=True,
            ),
            last_effective_market_trend=_require_float(
                round_state.get("last_effective_market_trend"),
                "round_state.last_effective_market_trend",
            ),
            event_probability=_require_float(
                settings.get("event_probability"),
                "settings.event_probability",
                minimum=0.0,
                maximum=1.0,
            ),
            pirate_attack_probability=_require_float(
                settings.get("pirate_attack_probability"),
                "settings.pirate_attack_probability",
                minimum=0.0,
                maximum=1.0,
            ),
        )


def save_game(
    engine: EconomyEngine,
    save_directory: Path = DEFAULT_SAVE_DIRECTORY,
    *,
    now: datetime | None = None,
) -> Path:
    """Write a timestamped save without overwriting an existing save."""
    saved_at = now if now is not None else datetime.now().astimezone()
    filename_stem = saved_at.strftime("%Y_%m_%d_%H_%M")
    data = SaveGameData.from_engine(engine, saved_at=saved_at)
    save_directory = Path(save_directory)

    try:
        save_directory.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=".galactic_trader_",
            suffix=".tmp",
            dir=save_directory,
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(
                    data.to_json_object(),
                    file,
                    indent=2,
                    sort_keys=True,
                    allow_nan=False,
                )
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            suffix_number = 1
            while True:
                suffix = "" if suffix_number == 1 else f"_{suffix_number:02d}"
                save_path = save_directory / f"{filename_stem}{suffix}.json"
                try:
                    os.link(temporary_path, save_path)
                except FileExistsError:
                    suffix_number += 1
                    continue
                return save_path
        finally:
            temporary_path.unlink(missing_ok=True)
    except (OSError, TypeError, ValueError) as error:
        raise SaveGameException(f"Could not save the game: {error}") from error


def load_game(
    save_name: str,
    save_directory: Path = DEFAULT_SAVE_DIRECTORY,
) -> EconomyEngine:
    """Load one named JSON save from the configured save directory."""
    save_path = _resolve_save_path(save_name, Path(save_directory))
    if not save_path.is_file():
        raise SaveGameNotFoundException(f"Save game '{save_path.stem}' does not exist.")

    try:
        with save_path.open(encoding="utf-8") as file:
            raw: object = json.load(file)
    except json.JSONDecodeError as error:
        raise InvalidSaveGameException(
            f"Save game '{save_path.stem}' does not contain valid JSON."
        ) from error
    except OSError as error:
        raise SaveGameException(f"Could not read the save game: {error}") from error

    data = SaveGameData.from_json_object(raw)
    return _restore_engine(data)


def list_save_games(
    save_directory: Path = DEFAULT_SAVE_DIRECTORY,
) -> tuple[Path, ...]:
    """Return save files in descending timestamp/filename order."""
    save_directory = Path(save_directory)
    if not save_directory.exists():
        return ()
    try:
        return tuple(
            sorted(
                (path for path in save_directory.glob("*.json") if path.is_file()),
                reverse=True,
            )
        )
    except OSError as error:
        raise SaveGameException(f"Could not list save games: {error}") from error


def _restore_engine(data: SaveGameData) -> EconomyEngine:
    """Build an engine from previously validated save data."""
    engine = EconomyEngine(
        event_probability=data.event_probability,
        pirate_attack_probability=data.pirate_attack_probability,
    )
    engine.player = Inventory(
        money=data.money,
        stock={
            _get_product(product_id, "player.stock"): quantity
            for product_id, quantity in data.stock.items()
        },
    )

    for product_id, market_data in data.markets.items():
        market = engine.markets[_get_product(product_id, "markets")]
        market.set_price(market_data.current_price)
        market.set_volatility(market_data.volatility)

    for product_id, direction in data.pending_price_directions.items():
        engine.pending_price_directions[
            _get_product(product_id, "pending_price_directions")
        ] = direction

    engine.history = list(data.history)
    for investment_id in data.investments:
        engine.investments.add(get_investment(investment_id))

    restored_fleet = Fleet()
    for ship_data in data.ships:
        model = get_ship_model(ship_data.model_id)
        mission_data = ship_data.active_transport
        mission = (
            None
            if mission_data is None
            else TransportMission(
                product=_get_product(
                    mission_data.product_id,
                    "fleet.active_transport.product_id",
                ),
                quantity=mission_data.quantity,
                total_rounds=mission_data.total_rounds,
                remaining_rounds=mission_data.remaining_rounds,
            )
        )
        if mission is not None:
            if not model.can_transport(mission.product):
                raise InvalidSaveGameException(
                    f"Ship #{ship_data.ship_id} cannot carry {mission.product}."
                )
            if mission.quantity > model.cargo_capacity:
                raise InvalidSaveGameException(
                    f"Ship #{ship_data.ship_id} exceeds its cargo capacity."
                )
        restored_fleet.restore_ship(
            ship_id=ship_data.ship_id,
            model=model,
            active_transport=mission,
        )

    try:
        restored_fleet.restore_next_ship_id(data.next_ship_id)
    except ValueError as error:
        raise InvalidSaveGameException(str(error)) from None
    engine.fleet = restored_fleet
    engine.restore_round_state(
        round_number=data.round_number,
        market_trend_index=data.market_trend_index,
        last_trend_multiplier=data.last_trend_multiplier,
        last_effective_market_trend=data.last_effective_market_trend,
    )
    return engine


def _resolve_save_path(save_name: str, save_directory: Path) -> Path:
    """Resolve a safe save name without allowing directory traversal."""
    normalized_name = save_name.strip()
    if normalized_name.lower().endswith(".json"):
        normalized_name = normalized_name[:-5]
    if not SAVE_NAME_PATTERN.fullmatch(normalized_name):
        raise SaveGameNotFoundException(
            "Save name may contain only letters, numbers, '-' and '_'."
        )
    return save_directory / f"{normalized_name}.json"


def _read_ship(raw: object, index: int) -> ShipSaveData:
    """Read and validate one ship from decoded JSON."""
    ship = _require_dict(raw, f"fleet.ships[{index}]")
    model_id = _require_string(
        ship.get("model_id"),
        f"fleet.ships[{index}].model_id",
    )
    try:
        get_ship_model(model_id)
    except UnknownShipModelException as error:
        raise InvalidSaveGameException(str(error)) from None

    transport_raw = ship.get("active_transport")
    transport: TransportSaveData | None = None
    if transport_raw is not None:
        transport_dict = _require_dict(
            transport_raw,
            f"fleet.ships[{index}].active_transport",
        )
        product_id = _require_string(
            transport_dict.get("product_id"),
            f"fleet.ships[{index}].active_transport.product_id",
        )
        _get_product(product_id, f"fleet.ships[{index}].active_transport")
        total_rounds = _require_int(
            transport_dict.get("total_rounds"),
            f"fleet.ships[{index}].active_transport.total_rounds",
            minimum=1,
        )
        transport = TransportSaveData(
            product_id=product_id,
            quantity=_require_int(
                transport_dict.get("quantity"),
                f"fleet.ships[{index}].active_transport.quantity",
                minimum=0,
            ),
            total_rounds=total_rounds,
            remaining_rounds=_require_int(
                transport_dict.get("remaining_rounds"),
                f"fleet.ships[{index}].active_transport.remaining_rounds",
                minimum=1,
                maximum=total_rounds,
            ),
        )

    return ShipSaveData(
        ship_id=_require_int(
            ship.get("ship_id"),
            f"fleet.ships[{index}].ship_id",
            minimum=1,
        ),
        model_id=model_id,
        active_transport=transport,
    )


def _read_history_entry(raw: object, index: int) -> HistoryEntry:
    """Read one four-value history entry."""
    entry = _require_list(raw, f"history[{index}]")
    if len(entry) != 4:
        raise InvalidSaveGameException(
            f"Field 'history[{index}]' must contain four values."
        )
    return (
        _require_string(entry[0], f"history[{index}][0]"),
        _require_string(entry[1], f"history[{index}][1]"),
        _require_int(entry[2], f"history[{index}][2]"),
        _require_float(entry[3], f"history[{index}][3]"),
    )


def _read_int_mapping(
    raw: object,
    field_name: str,
    *,
    minimum: int | None = None,
) -> dict[str, int]:
    """Read a string-to-integer mapping."""
    mapping = _require_dict(raw, field_name)
    return {
        key: _require_int(
            value,
            f"{field_name}.{key}",
            minimum=minimum,
        )
        for key, value in mapping.items()
    }


def _get_product(product_id: str, field_name: str) -> Product:
    """Resolve a stable product identifier from save data."""
    try:
        return Product[product_id]
    except KeyError:
        raise InvalidSaveGameException(
            f"Field '{field_name}' contains unknown product '{product_id}'."
        ) from None


def _require_dict(raw: object, field_name: str) -> dict[str, object]:
    """Require a JSON object with string keys."""
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        raise InvalidSaveGameException(f"Field '{field_name}' must be a JSON object.")
    return cast(dict[str, object], raw)


def _require_list(raw: object, field_name: str) -> list[object]:
    """Require a JSON array."""
    if not isinstance(raw, list):
        raise InvalidSaveGameException(f"Field '{field_name}' must be a JSON array.")
    return cast(list[object], raw)


def _require_string(raw: object, field_name: str) -> str:
    """Require a non-empty string."""
    if not isinstance(raw, str) or not raw.strip():
        raise InvalidSaveGameException(
            f"Field '{field_name}' must be a non-empty string."
        )
    return raw


def _require_int(
    raw: object,
    field_name: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Require an integer within optional inclusive limits."""
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise InvalidSaveGameException(f"Field '{field_name}' must be a whole number.")
    if minimum is not None and raw < minimum:
        raise InvalidSaveGameException(
            f"Field '{field_name}' must be at least {minimum}."
        )
    if maximum is not None and raw > maximum:
        raise InvalidSaveGameException(
            f"Field '{field_name}' must be at most {maximum}."
        )
    return raw


def _require_float(
    raw: object,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    minimum_exclusive: bool = False,
) -> float:
    """Require a finite number within optional limits."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise InvalidSaveGameException(f"Field '{field_name}' must be a number.")
    value = float(raw)
    if not (float("-inf") < value < float("inf")):
        raise InvalidSaveGameException(f"Field '{field_name}' must be finite.")
    if minimum is not None:
        below_minimum = value <= minimum if minimum_exclusive else value < minimum
        if below_minimum:
            comparison = "greater than" if minimum_exclusive else "at least"
            raise InvalidSaveGameException(
                f"Field '{field_name}' must be {comparison} {minimum}."
            )
    if maximum is not None and value > maximum:
        raise InvalidSaveGameException(
            f"Field '{field_name}' must be at most {maximum}."
        )
    return value
