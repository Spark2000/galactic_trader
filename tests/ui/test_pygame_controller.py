"""Tests for the UI-facing pygame controller."""

from datetime import UTC, datetime
from pathlib import Path

from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product
from galactic_trader.savegame import save_game
from galactic_trader.ships import get_ship_model
from galactic_trader.ui.pygame_ui.controller import GameController


def test_controller_buys_product_with_selected_transport(tmp_path: Path) -> None:
    """A graphical purchase delegates to the existing transport rules."""
    engine = EconomyEngine()
    engine.player.money = 1_000.0
    ship = engine.buy_ship("refrigerated_s_1")[0]
    controller = GameController(engine, save_directory=tmp_path)

    options = controller.transport_options(Product.FOOD, 3)
    purchase = controller.buy_product(Product.FOOD, 3, options[0].ship_id)

    assert purchase.ship_id == ship.ship_id
    assert purchase.quantity == 3
    assert ship.active_transport is not None


def test_controller_exposes_ship_and_round_actions(tmp_path: Path) -> None:
    """Fleet actions and round progression remain owned by the engine."""
    engine = EconomyEngine(event_probability=0, pirate_attack_probability=0)
    engine.player.money = 1_000.0
    controller = GameController(engine, save_directory=tmp_path)
    model = get_ship_model("standard_s_1")

    owned_ship, purchase_price = controller.buy_ship(model)
    round_result = controller.advance_round()
    sold_ship, sale_price = controller.sell_ship(owned_ship.ship_id)

    assert purchase_price == model.purchase_price
    assert round_result.market_event is None
    assert sold_ship == owned_ship
    assert sale_price == model.purchase_price * 0.70


def test_controller_load_replaces_the_active_engine(tmp_path: Path) -> None:
    """Loading swaps the engine used by all following pygame actions."""
    saved_engine = EconomyEngine()
    saved_engine.player.money = 777.0
    save_path = save_game(
        saved_engine,
        tmp_path,
        now=datetime(2026, 8, 31, 12, 30, tzinfo=UTC),
    )
    controller = GameController(EconomyEngine(), save_directory=tmp_path)

    loaded = controller.load(save_path.stem)

    assert controller.engine is loaded
    assert loaded.player.money == 777.0
    assert controller.available_saves() == (save_path,)
