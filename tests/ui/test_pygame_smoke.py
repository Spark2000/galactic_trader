"""Headless smoke tests for pygame-ce rendering."""

from pathlib import Path

import pytest

from galactic_trader.engine import EconomyEngine
from galactic_trader.products import Product


def test_all_pygame_views_and_trade_dialog_render_headlessly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every primary screen and the two-stage purchase flow can draw in CI."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    import pygame

    from galactic_trader.ui.pygame_ui.app import DialogKind, PygameUI, View

    engine = EconomyEngine(event_probability=0, pirate_attack_probability=0)
    engine.player.money = 10_000.0
    engine.buy_ship("refrigerated_s_1")
    ui = PygameUI(engine, save_directory=tmp_path, window_size=(960, 600))

    for view in View:
        ui.view = view
        ui._draw()

    ui._open_trade_dialog(Product.FOOD, "buy")
    ui._draw()
    ui._confirm_trade()
    assert ui.dialog is not None
    assert ui.dialog.kind is DialogKind.TRANSPORT
    ui._draw()

    assert ui.surface.get_size() == (960, 600)
    assert ui.hit_targets
    pygame.quit()
