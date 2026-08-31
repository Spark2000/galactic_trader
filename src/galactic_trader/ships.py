"""Spaceship model definitions and their market registry."""

from dataclasses import dataclass
from typing import Final

from galactic_trader.cargo import CargoType
from galactic_trader.exceptions import UnknownShipModelException
from galactic_trader.products import Product


@dataclass(frozen=True)
class ShipModel:
    """Describe the fixed properties of a purchasable spaceship model."""

    model_id: str
    display_name: str
    cargo_type: CargoType
    cargo_capacity: int
    speed_rating: int
    defense_rating: int
    purchase_price: float

    def __post_init__(self) -> None:
        """Validate the spaceship model values."""
        if not self.model_id.isidentifier() or self.model_id != self.model_id.lower():
            raise ValueError(
                "Model ID must be a lowercase identifier, for example 'atlas_runner'."
            )
        if not self.display_name.strip():
            raise ValueError("Display name must not be empty.")
        if not isinstance(self.cargo_type, CargoType):
            raise TypeError("Cargo type must be an instance of CargoType.")
        if self.cargo_capacity <= 0:
            raise ValueError("Cargo capacity must be greater than zero.")
        if not 0 <= self.speed_rating <= 100:
            raise ValueError("Speed rating must be between zero and one hundred.")
        if not 0 <= self.defense_rating <= 100:
            raise ValueError("Defense rating must be between zero and one hundred.")
        if self.purchase_price <= 0:
            raise ValueError("Purchase price must be greater than zero.")

    def can_transport(self, product: Product) -> bool:
        """Return whether this model can transport a product."""
        return self.cargo_type is product.cargo_type

    def __str__(self) -> str:
        """Return the user-facing spaceship model name."""
        return self.display_name


SHIP_MODELS: Final[tuple[ShipModel, ...]] = (
    # standard
    ShipModel(
        model_id="standard_s_1",
        display_name="Comet Courier",
        cargo_type=CargoType.STANDARD,
        cargo_capacity=10,
        speed_rating=90,
        defense_rating=20,
        purchase_price=80.0,
    ),
    ShipModel(
        model_id="standard_m_1",
        display_name="Comet Freighter",
        cargo_type=CargoType.STANDARD,
        cargo_capacity=30,
        speed_rating=70,
        defense_rating=45,
        purchase_price=300.0,
    ),
    ShipModel(
        model_id="standard_l_1",
        display_name="Comet Hauler",
        cargo_type=CargoType.STANDARD,
        cargo_capacity=70,
        speed_rating=50,
        defense_rating=75,
        purchase_price=900.0,
    ),
    # liquid
    ShipModel(
        model_id="liquid_s_1",
        display_name="Orca Courier",
        cargo_type=CargoType.LIQUID,
        cargo_capacity=8,
        speed_rating=85,
        defense_rating=25,
        purchase_price=110.0,
    ),
    ShipModel(
        model_id="liquid_m_1",
        display_name="Orca Freighter",
        cargo_type=CargoType.LIQUID,
        cargo_capacity=24,
        speed_rating=65,
        defense_rating=50,
        purchase_price=390.0,
    ),
    ShipModel(
        model_id="liquid_l_1",
        display_name="Orca Hauler",
        cargo_type=CargoType.LIQUID,
        cargo_capacity=56,
        speed_rating=45,
        defense_rating=80,
        purchase_price=1100.0,
    ),
    # refrigerated
    ShipModel(
        model_id="refrigerated_s_1",
        display_name="Polar Courier",
        cargo_type=CargoType.REFRIGERATED,
        cargo_capacity=8,
        speed_rating=88,
        defense_rating=25,
        purchase_price=130.0,
    ),
    ShipModel(
        model_id="refrigerated_m_1",
        display_name="Polar Freighter",
        cargo_type=CargoType.REFRIGERATED,
        cargo_capacity=22,
        speed_rating=68,
        defense_rating=50,
        purchase_price=450.0,
    ),
    ShipModel(
        model_id="refrigerated_l_1",
        display_name="Polar Hauler",
        cargo_type=CargoType.REFRIGERATED,
        cargo_capacity=52,
        speed_rating=48,
        defense_rating=82,
        purchase_price=1280.0,
    ),
    # hazardous
    ShipModel(
        model_id="hazardous_s_1",
        display_name="Nebula Courier",
        cargo_type=CargoType.HAZARDOUS,
        cargo_capacity=6,
        speed_rating=80,
        defense_rating=40,
        purchase_price=180.0,
    ),
    ShipModel(
        model_id="hazardous_m_1",
        display_name="Nebula Freighter",
        cargo_type=CargoType.HAZARDOUS,
        cargo_capacity=18,
        speed_rating=60,
        defense_rating=70,
        purchase_price=620.0,
    ),
    ShipModel(
        model_id="hazardous_l_1",
        display_name="Nebula Hauler",
        cargo_type=CargoType.HAZARDOUS,
        cargo_capacity=42,
        speed_rating=42,
        defense_rating=100,
        purchase_price=1750.0,
    ),
    # specialized models:
    ShipModel(
        model_id="atlas_runner",
        display_name="Atlas Runner",
        cargo_type=CargoType.REFRIGERATED,
        cargo_capacity=12,
        speed_rating=100,
        defense_rating=50,
        purchase_price=950.0,
    ),
    ShipModel(
        model_id="leviathan_tanker",
        display_name="Leviathan Tanker",
        cargo_type=CargoType.LIQUID,
        cargo_capacity=100,
        speed_rating=25,
        defense_rating=100,
        purchase_price=2000.0,
    ),
    ShipModel(
        model_id="titan_carrier",
        display_name="Titan Carrier",
        cargo_type=CargoType.HAZARDOUS,
        cargo_capacity=100,
        speed_rating=25,
        defense_rating=100,
        purchase_price=2200.0,
    ),
)


def get_ship_model(model_id: str) -> ShipModel:
    """Return the spaceship model with the requested model ID."""
    normalized_id = model_id.strip().lower()

    for model in SHIP_MODELS:
        if model.model_id == normalized_id:
            return model

    available_ids = ", ".join(model.model_id for model in SHIP_MODELS)
    raise UnknownShipModelException(
        f"Unknown spaceship model '{model_id}'. Available model IDs: {available_ids}."
    )


def get_ship_models(cargo_type: CargoType) -> tuple[ShipModel, ...]:
    """Return every spaceship model supporting a cargo type."""
    return tuple(model for model in SHIP_MODELS if model.cargo_type is cargo_type)


def get_all_ship_models() -> tuple[ShipModel, ...]:
    """Return every registered spaceship model."""
    return SHIP_MODELS
