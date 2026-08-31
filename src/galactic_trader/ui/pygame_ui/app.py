"""Interactive pygame-ce command-deck interface for Galactic Trader."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from time import monotonic
from typing import Final

import pygame

from galactic_trader.engine import EconomyEngine, RoundResult
from galactic_trader.exceptions import GameException
from galactic_trader.investments import Investment
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product
from galactic_trader.savegame import DEFAULT_SAVE_DIRECTORY
from galactic_trader.ships import ShipModel, get_all_ship_models
from galactic_trader.transport import TransportOption
from galactic_trader.ui.pygame_ui.controller import GameController
from galactic_trader.ui.pygame_ui.theme import (
    MIN_WINDOW_SIZE,
    PALETTE,
    SIDEBAR_WIDTH,
    TOP_BAR_HEIGHT,
    WINDOW_SIZE,
    Fonts,
    create_fonts,
)
from galactic_trader.ui.pygame_ui.widgets import (
    HitTarget,
    draw_button,
    draw_panel,
    draw_progress,
    draw_text,
    draw_wrapped_text,
    ellipsize,
)

FPS: Final[int] = 60
CONTENT_PADDING: Final[int] = 24


class View(Enum):
    """Top-level game screens."""

    MARKET = auto()
    PRODUCTION = auto()
    FLEET = auto()
    INVESTMENTS = auto()


class FleetMode(Enum):
    """Subsections of the fleet screen."""

    OWNED = auto()
    SHIPYARD = auto()


class DialogKind(Enum):
    """Modal flows supported by the UI."""

    TRADE = auto()
    TRANSPORT = auto()
    PRODUCE = auto()
    BUY_SHIP = auto()
    SELL_SHIP = auto()
    BUY_INVESTMENT = auto()
    LOAD = auto()
    ROUND_REPORT = auto()
    QUIT = auto()


@dataclass
class DialogState:
    """Mutable state for the currently open modal dialog."""

    kind: DialogKind
    product: Product | None = None
    trade_action: str | None = None
    quantity: int = 1
    ship_model: ShipModel | None = None
    ship_id: int | None = None
    investment: Investment | None = None
    transport_options: tuple[TransportOption, ...] = ()
    save_paths: tuple[Path, ...] = ()
    round_result: RoundResult | None = None
    message: str = ""
    scroll: int = 0


@dataclass
class Toast:
    """Short-lived non-blocking feedback message."""

    message: str
    is_error: bool = False
    expires_at: float = field(default_factory=lambda: monotonic() + 3.2)


class PygameUI:
    """Render and operate Galactic Trader with pygame-ce."""

    def __init__(
        self,
        engine: EconomyEngine,
        *,
        save_directory: Path = DEFAULT_SAVE_DIRECTORY,
        window_size: tuple[int, int] = WINDOW_SIZE,
    ) -> None:
        """Initialize pygame, presentation state and the game controller."""
        pygame.init()
        pygame.display.set_caption("Galactic Trader")
        width = max(MIN_WINDOW_SIZE[0], window_size[0])
        height = max(MIN_WINDOW_SIZE[1], window_size[1])
        self.surface = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.fonts: Fonts = create_fonts()
        self.controller = GameController(engine, save_directory=save_directory)

        self.running = False
        self.view = View.MARKET
        self.fleet_mode = FleetMode.OWNED
        self.dialog: DialogState | None = None
        self.toast: Toast | None = None
        self.hit_targets: list[HitTarget] = []
        self.scroll_offsets: dict[View, int] = {view: 0 for view in View}
        self.max_scroll: dict[View, int] = {view: 0 for view in View}

    @property
    def engine(self) -> EconomyEngine:
        """Return the controller's currently active engine."""
        return self.controller.engine

    def run(self) -> None:
        """Run the pygame event loop until the player quits."""
        self.running = True
        while self.running:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def _handle_events(self) -> None:
        """Process one frame of window, keyboard, wheel and click events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._open_quit_dialog()
            elif event.type == pygame.VIDEORESIZE:
                width = max(MIN_WINDOW_SIZE[0], event.w)
                height = max(MIN_WINDOW_SIZE[1], event.h)
                self.surface = pygame.display.set_mode(
                    (width, height), pygame.RESIZABLE
                )
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_wheel(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle keyboard shortcuts and dialog cancellation."""
        if event.key == pygame.K_ESCAPE:
            if self.dialog is not None:
                self.dialog = None
            else:
                self._open_quit_dialog()
            return
        if self.dialog is not None:
            if event.key in {pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS}:
                self._adjust_quantity(1)
            elif event.key in {pygame.K_MINUS, pygame.K_KP_MINUS}:
                self._adjust_quantity(-1)
            return

        if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_s:
            self._save_game()
        elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_l:
            self._open_load_dialog()
        elif event.key == pygame.K_1:
            self.view = View.MARKET
        elif event.key == pygame.K_2:
            self.view = View.PRODUCTION
        elif event.key == pygame.K_3:
            self.view = View.FLEET
        elif event.key == pygame.K_4:
            self.view = View.INVESTMENTS
        elif event.key == pygame.K_n:
            self._advance_round()
        elif event.key == pygame.K_q:
            self._open_quit_dialog()

    def _handle_wheel(self, direction: int) -> None:
        """Scroll the active screen or scrollable modal."""
        delta = direction * 52
        if self.dialog is not None and self.dialog.kind in {
            DialogKind.TRANSPORT,
            DialogKind.LOAD,
            DialogKind.ROUND_REPORT,
        }:
            self.dialog.scroll = max(0, self.dialog.scroll - delta)
            return
        current = self.scroll_offsets[self.view]
        self.scroll_offsets[self.view] = max(
            0,
            min(self.max_scroll[self.view], current - delta),
        )

    def _handle_click(self, position: tuple[int, int]) -> None:
        """Activate the uppermost enabled target below the pointer."""
        modal_open = self.dialog is not None
        for target in reversed(self.hit_targets):
            if target.modal != modal_open:
                continue
            if target.enabled and target.rect.collidepoint(position):
                self._trigger(target.action, target.payload)
                return

    def _trigger(self, action: str, payload: object | None) -> None:
        """Dispatch one declarative hit target action."""
        if action == "view" and isinstance(payload, View):
            self.view = payload
        elif action == "fleet_mode" and isinstance(payload, FleetMode):
            self.fleet_mode = payload
            self.scroll_offsets[View.FLEET] = 0
        elif action == "save":
            self._save_game()
        elif action == "load":
            self._open_load_dialog()
        elif action == "quit":
            self._open_quit_dialog()
        elif action == "next_round":
            self._advance_round()
        elif action == "close_dialog":
            self.dialog = None
        elif action == "adjust_quantity" and isinstance(payload, int):
            self._adjust_quantity(payload)
        elif action == "open_buy" and isinstance(payload, Product):
            self._open_trade_dialog(payload, "buy")
        elif action == "open_sell" and isinstance(payload, Product):
            self._open_trade_dialog(payload, "sell")
        elif action == "confirm_trade":
            self._confirm_trade()
        elif action == "choose_transport" and isinstance(payload, int):
            self._complete_purchase(payload)
        elif action == "transport_back" and self.dialog is not None:
            self.dialog.kind = DialogKind.TRADE
            self.dialog.message = ""
        elif action == "open_produce" and isinstance(payload, Product):
            self.dialog = DialogState(kind=DialogKind.PRODUCE, product=payload)
        elif action == "confirm_produce":
            self._confirm_production()
        elif action == "open_buy_ship" and isinstance(payload, ShipModel):
            self.dialog = DialogState(kind=DialogKind.BUY_SHIP, ship_model=payload)
        elif action == "confirm_buy_ship":
            self._confirm_buy_ship()
        elif action == "open_sell_ship" and isinstance(payload, int):
            self.dialog = DialogState(kind=DialogKind.SELL_SHIP, ship_id=payload)
        elif action == "confirm_sell_ship":
            self._confirm_sell_ship()
        elif action == "open_investment" and isinstance(payload, Investment):
            self.dialog = DialogState(
                kind=DialogKind.BUY_INVESTMENT,
                investment=payload,
            )
        elif action == "confirm_investment":
            self._confirm_investment()
        elif action == "choose_save" and isinstance(payload, Path):
            self._load_game(payload.stem)
        elif action == "confirm_quit":
            self.running = False

    def _open_trade_dialog(self, product: Product, action: str) -> None:
        """Start a product purchase or sale flow."""
        self.dialog = DialogState(
            kind=DialogKind.TRADE,
            product=product,
            trade_action=action,
        )

    def _adjust_quantity(self, change: int) -> None:
        """Change the active trade or production amount."""
        if self.dialog is None or self.dialog.kind not in {
            DialogKind.TRADE,
            DialogKind.PRODUCE,
        }:
            return
        self.dialog.quantity = max(1, self.dialog.quantity + change)
        self.dialog.message = ""

    def _confirm_trade(self) -> None:
        """Complete a sale or continue a purchase with ship selection."""
        if self.dialog is None or self.dialog.product is None:
            return
        product = self.dialog.product
        quantity = self.dialog.quantity
        if self.dialog.trade_action == "sell":
            try:
                _, unit_price = self.controller.sell_product(product, quantity)
            except (GameException, ValueError) as error:
                self.dialog.message = str(error)
                return
            self.dialog = None
            self._show_toast(
                f"Sold {quantity} {product} at {unit_price:.2f} Credits each."
            )
            return

        try:
            options = self.controller.transport_options(product, quantity)
        except (GameException, ValueError) as error:
            self.dialog.message = str(error)
            return
        if not options:
            self.dialog.message = (
                "No available ship has the required cargo type and capacity."
            )
            return
        self.dialog.kind = DialogKind.TRANSPORT
        self.dialog.transport_options = options
        self.dialog.message = ""
        self.dialog.scroll = 0

    def _complete_purchase(self, ship_id: int) -> None:
        """Buy the selected goods and launch the selected ship."""
        if self.dialog is None or self.dialog.product is None:
            return
        product = self.dialog.product
        quantity = self.dialog.quantity
        try:
            purchase = self.controller.buy_product(product, quantity, ship_id)
        except (GameException, ValueError) as error:
            self.dialog.message = str(error)
            return
        self.dialog = None
        self._show_toast(
            f"Bought {purchase.quantity} {purchase.product}. "
            f"{purchase.ship_name} returns in {purchase.travel_rounds} round(s)."
        )

    def _confirm_production(self) -> None:
        """Produce the amount selected in the open production dialog."""
        if self.dialog is None or self.dialog.product is None:
            return
        product = self.dialog.product
        quantity = self.dialog.quantity
        try:
            _, total_cost = self.controller.produce_product(product, quantity)
        except (GameException, ValueError) as error:
            self.dialog.message = str(error)
            return
        self.dialog = None
        self._show_toast(
            f"Produced {quantity} {product} for {total_cost:.2f} Credits."
        )

    def _confirm_buy_ship(self) -> None:
        """Buy the ship model shown in the open confirmation dialog."""
        if self.dialog is None or self.dialog.ship_model is None:
            return
        try:
            ship, price = self.controller.buy_ship(self.dialog.ship_model)
        except (GameException, ValueError) as error:
            self.dialog.message = str(error)
            return
        self.dialog = None
        self._show_toast(f"Bought {ship} for {price:.2f} Credits.")

    def _confirm_sell_ship(self) -> None:
        """Sell the ship selected by the player."""
        if self.dialog is None or self.dialog.ship_id is None:
            return
        try:
            ship, price = self.controller.sell_ship(self.dialog.ship_id)
        except (GameException, ValueError) as error:
            self.dialog.message = str(error)
            return
        self.dialog = None
        self._show_toast(f"Sold {ship} for {price:.2f} Credits.")

    def _confirm_investment(self) -> None:
        """Buy the investment shown in the open dialog."""
        if self.dialog is None or self.dialog.investment is None:
            return
        try:
            investment, price = self.controller.buy_investment(
                self.dialog.investment
            )
        except (GameException, ValueError) as error:
            self.dialog.message = str(error)
            return
        self.dialog = None
        self._show_toast(f"Bought {investment} for {price:.2f} Credits.")

    def _save_game(self) -> None:
        """Save the game and report the generated filename."""
        try:
            path = self.controller.save()
        except (GameException, ValueError) as error:
            self._show_toast(str(error), is_error=True)
            return
        self._show_toast(f"Game saved as '{path.stem}'.")

    def _open_load_dialog(self) -> None:
        """Open a dialog containing every loadable save game."""
        try:
            paths = self.controller.available_saves()
        except (GameException, ValueError) as error:
            self._show_toast(str(error), is_error=True)
            return
        self.dialog = DialogState(kind=DialogKind.LOAD, save_paths=paths)

    def _load_game(self, save_name: str) -> None:
        """Load and activate a named save game."""
        try:
            self.controller.load(save_name)
        except (GameException, ValueError) as error:
            if self.dialog is not None:
                self.dialog.message = str(error)
            return
        self.dialog = None
        self._show_toast(f"Game '{save_name}' loaded.")

    def _advance_round(self) -> None:
        """Advance the simulation and open the round report."""
        try:
            result = self.controller.advance_round()
        except (GameException, ValueError) as error:
            self._show_toast(str(error), is_error=True)
            return
        self.dialog = DialogState(
            kind=DialogKind.ROUND_REPORT,
            round_result=result,
        )

    def _open_quit_dialog(self) -> None:
        """Request confirmation before closing the game window."""
        self.dialog = DialogState(kind=DialogKind.QUIT)

    def _show_toast(self, message: str, *, is_error: bool = False) -> None:
        """Display short feedback in the bottom-right corner."""
        self.toast = Toast(message=message, is_error=is_error)

    def _draw(self) -> None:
        """Draw one complete interface frame."""
        self.hit_targets.clear()
        self.surface.fill(PALETTE.space)
        self._draw_top_bar()
        self._draw_sidebar()

        content_rect = pygame.Rect(
            SIDEBAR_WIDTH,
            TOP_BAR_HEIGHT,
            self.surface.get_width() - SIDEBAR_WIDTH,
            self.surface.get_height() - TOP_BAR_HEIGHT,
        )
        if self.view is View.MARKET:
            self._draw_market(content_rect)
        elif self.view is View.PRODUCTION:
            self._draw_production(content_rect)
        elif self.view is View.FLEET:
            self._draw_fleet(content_rect)
        else:
            self._draw_investments(content_rect)

        if self.toast is not None:
            if monotonic() >= self.toast.expires_at:
                self.toast = None
            else:
                self._draw_toast(self.toast)
        if self.dialog is not None:
            self._draw_dialog(self.dialog)

    def _draw_top_bar(self) -> None:
        """Draw the persistent brand, round, credits and file actions."""
        width = self.surface.get_width()
        pygame.draw.rect(
            self.surface,
            PALETTE.deep,
            pygame.Rect(0, 0, width, TOP_BAR_HEIGHT),
        )
        pygame.draw.line(
            self.surface,
            PALETTE.edge,
            (0, TOP_BAR_HEIGHT - 1),
            (width, TOP_BAR_HEIGHT - 1),
        )
        pygame.draw.circle(self.surface, PALETTE.cyan_soft, (30, 36), 20)
        pygame.draw.circle(self.surface, PALETTE.cyan, (30, 36), 9, width=2)
        pygame.draw.circle(self.surface, PALETTE.cyan, (30, 36), 3)
        draw_text(
            self.surface,
            self.fonts.body_bold,
            "GALACTIC TRADER",
            PALETTE.text,
            (58, 19),
        )
        draw_text(
            self.surface,
            self.fonts.tiny,
            "CORE SECTOR · COMMAND DECK",
            PALETTE.muted,
            (58, 43),
        )

        status_width = 136
        credits_rect = pygame.Rect(width - 440, 14, status_width, 44)
        round_rect = pygame.Rect(width - 296, 14, 92, 44)
        self._draw_status_box(credits_rect, "CREDITS", f"{self.engine.player.money:,.2f}")
        self._draw_status_box(round_rect, "ROUND", str(self.engine.round_number))

        self._button(
            pygame.Rect(width - 194, 18, 54, 36),
            "Save",
            "save",
            compact=True,
        )
        self._button(
            pygame.Rect(width - 134, 18, 54, 36),
            "Load",
            "load",
            compact=True,
        )
        self._button(
            pygame.Rect(width - 74, 18, 54, 36),
            "Quit",
            "quit",
            compact=True,
        )

    def _draw_status_box(self, rect: pygame.Rect, label: str, value: str) -> None:
        """Draw one compact numeric item in the top bar."""
        draw_panel(self.surface, rect, color=PALETTE.panel_alt, radius=8)
        draw_text(
            self.surface,
            self.fonts.tiny,
            label,
            PALETTE.muted,
            (rect.centerx, rect.y + 6),
            anchor="midtop",
        )
        draw_text(
            self.surface,
            self.fonts.small,
            value,
            PALETTE.text,
            (rect.centerx, rect.bottom - 7),
            anchor="midbottom",
        )

    def _draw_sidebar(self) -> None:
        """Draw persistent navigation and the next-round action."""
        height = self.surface.get_height()
        rect = pygame.Rect(0, TOP_BAR_HEIGHT, SIDEBAR_WIDTH, height - TOP_BAR_HEIGHT)
        pygame.draw.rect(self.surface, PALETTE.deep, rect)
        pygame.draw.line(
            self.surface,
            PALETTE.edge,
            (SIDEBAR_WIDTH - 1, TOP_BAR_HEIGHT),
            (SIDEBAR_WIDTH - 1, height),
        )
        labels = (
            (View.MARKET, "1  Market"),
            (View.PRODUCTION, "2  Production"),
            (View.FLEET, "3  Fleet"),
            (View.INVESTMENTS, "4  Investments"),
        )
        y = TOP_BAR_HEIGHT + 20
        for view, label in labels:
            self._button(
                pygame.Rect(14, y, SIDEBAR_WIDTH - 28, 44),
                label,
                "view",
                view,
                selected=self.view is view,
            )
            y += 52

        hint_rect = pygame.Rect(18, height - 132, SIDEBAR_WIDTH - 36, 50)
        draw_wrapped_text(
            self.surface,
            self.fonts.tiny,
            "Advancing applies prices, events and active transports.",
            PALETTE.muted,
            hint_rect,
            line_gap=1,
            max_lines=3,
        )
        self._button(
            pygame.Rect(14, height - 68, SIDEBAR_WIDTH - 28, 48),
            "Next round  N",
            "next_round",
            primary=True,
        )

    def _draw_page_heading(
        self,
        content: pygame.Rect,
        eyebrow: str,
        title: str,
        description: str,
    ) -> int:
        """Draw a standard screen heading and return the following y position."""
        x = content.x + CONTENT_PADDING
        y = content.y + 20
        draw_text(self.surface, self.fonts.tiny, eyebrow, PALETTE.cyan, (x, y))
        draw_text(
            self.surface,
            self.fonts.title,
            title,
            PALETTE.text,
            (x, y + 18),
        )
        draw_text(
            self.surface,
            self.fonts.small,
            description,
            PALETTE.muted,
            (x, y + 58),
        )
        return y + 91

    def _draw_market(self, content: pygame.Rect) -> None:
        """Draw live prices, inventory amounts and trading actions."""
        y = self._draw_page_heading(
            content,
            "TRADING DESK",
            "Sector market",
            "Buy goods, sell inventory and dispatch compatible transport ships.",
        )
        x = content.x + CONTENT_PADDING
        width = content.width - CONTENT_PADDING * 2
        notice_rect = pygame.Rect(x, y, width, 38)
        pygame.draw.rect(self.surface, PALETTE.cyan_soft, notice_rect, border_radius=8)
        pygame.draw.rect(
            self.surface,
            PALETTE.cyan,
            pygame.Rect(notice_rect.x, notice_rect.y, 3, notice_rect.height),
            border_radius=2,
        )
        event_text = (
            self.engine.last_market_event.message
            if self.engine.last_market_event is not None
            else "Market stable · No market event occurred in the previous round."
        )
        draw_text(
            self.surface,
            self.fonts.small,
            ellipsize(self.fonts.small, event_text, width - 28),
            PALETTE.text,
            (x + 16, y + 11),
        )

        history_height = 72
        table_rect = pygame.Rect(
            x,
            y + 50,
            width,
            content.bottom - (y + 50) - history_height - 20,
        )
        draw_panel(self.surface, table_rect)
        header_height = 38
        header_rect = pygame.Rect(
            table_rect.x,
            table_rect.y,
            table_rect.width,
            header_height,
        )
        pygame.draw.rect(
            self.surface,
            PALETTE.panel_alt,
            header_rect,
            border_top_left_radius=10,
            border_top_right_radius=10,
        )
        columns = self._market_columns(table_rect)
        for label, column_x in zip(
            ("PRODUCT", "ORIGIN", "PRICE", "STOCK", "ACTIONS"),
            columns,
            strict=True,
        ):
            draw_text(
                self.surface,
                self.fonts.tiny,
                label,
                PALETTE.muted,
                (column_x, header_rect.y + 13),
            )

        viewport = pygame.Rect(
            table_rect.x + 1,
            table_rect.y + header_height,
            table_rect.width - 2,
            table_rect.height - header_height - 1,
        )
        row_height = 54
        total_height = len(Product) * row_height
        self.max_scroll[View.MARKET] = max(0, total_height - viewport.height)
        scroll = min(self.scroll_offsets[View.MARKET], self.max_scroll[View.MARKET])
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        for index, product in enumerate(Product):
            row = pygame.Rect(
                viewport.x,
                viewport.y + index * row_height - scroll,
                viewport.width,
                row_height,
            )
            if row.bottom < viewport.top or row.top > viewport.bottom:
                continue
            self._draw_market_row(row, product, columns, viewport)
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, scroll)

        history_rect = pygame.Rect(x, table_rect.bottom + 10, width, history_height)
        self._draw_history(history_rect)

    def _market_columns(self, table_rect: pygame.Rect) -> tuple[int, ...]:
        """Return responsive x positions for the market table columns."""
        inner_x = table_rect.x + 15
        usable = table_rect.width - 30
        return (
            inner_x,
            inner_x + round(usable * 0.25),
            inner_x + round(usable * 0.46),
            inner_x + round(usable * 0.60),
            inner_x + round(usable * 0.70),
        )

    def _draw_market_row(
        self,
        row: pygame.Rect,
        product: Product,
        columns: tuple[int, ...],
        viewport: pygame.Rect,
    ) -> None:
        """Draw one market row and its buy/sell targets."""
        if list(Product).index(product) % 2:
            pygame.draw.rect(self.surface, PALETTE.deep, row)
        pygame.draw.line(
            self.surface,
            PALETTE.edge,
            (row.x, row.bottom - 1),
            (row.right, row.bottom - 1),
        )
        center_y = row.centery
        pygame.draw.rect(
            self.surface,
            self._cargo_color(product),
            pygame.Rect(columns[0], row.y + 14, 5, 26),
            border_radius=3,
        )
        draw_text(
            self.surface,
            self.fonts.small,
            product.display_name,
            PALETTE.text,
            (columns[0] + 13, row.y + 9),
        )
        draw_text(
            self.surface,
            self.fonts.tiny,
            str(product.cargo_type),
            PALETTE.muted,
            (columns[0] + 13, row.y + 31),
        )
        draw_text(
            self.surface,
            self.fonts.small,
            product.planet.display_name,
            PALETTE.text,
            (columns[1], row.y + 9),
        )
        draw_text(
            self.surface,
            self.fonts.tiny,
            f"Distance {product.distance}",
            PALETTE.muted,
            (columns[1], row.y + 31),
        )
        price = self.engine.markets[product].current_price
        draw_text(
            self.surface,
            self.fonts.small,
            f"{price:.2f} C",
            PALETTE.text,
            (columns[2], center_y),
            anchor="midleft",
        )
        stock = self.engine.player.stock.get(product, 0)
        draw_text(
            self.surface,
            self.fonts.small,
            str(stock),
            PALETTE.text if stock else PALETTE.muted,
            (columns[3], center_y),
            anchor="midleft",
        )
        button_gap = 6
        available = row.right - columns[4] - 14
        button_width = max(54, (available - button_gap) // 2)
        buy_rect = pygame.Rect(columns[4], row.y + 10, button_width, 34)
        sell_rect = pygame.Rect(
            columns[4] + button_width + button_gap,
            row.y + 10,
            button_width,
            34,
        )
        visible = row.top >= viewport.top and row.bottom <= viewport.bottom
        self._button(
            buy_rect,
            "Buy",
            "open_buy",
            product,
            primary=True,
            compact=True,
            register=visible,
        )
        self._button(
            sell_rect,
            "Sell",
            "open_sell",
            product,
            enabled=stock > 0,
            compact=True,
            register=visible,
        )

    def _draw_history(self, rect: pygame.Rect) -> None:
        """Draw the three most recent engine history records."""
        draw_panel(self.surface, rect)
        draw_text(
            self.surface,
            self.fonts.tiny,
            "RECENT ACTIVITY",
            PALETTE.muted,
            (rect.x + 13, rect.y + 10),
        )
        entries = self.engine.history[-3:]
        if not entries:
            draw_text(
                self.surface,
                self.fonts.small,
                "No transactions yet.",
                PALETTE.muted,
                (rect.x + 13, rect.y + 36),
            )
            return
        start_x = rect.x + 13
        slot_width = max(1, (rect.width - 26) // 3)
        for index, entry in enumerate(reversed(entries)):
            action, item, quantity, value = entry
            x = start_x + index * slot_width
            text = f"{action.replace('_', ' ').title()} · {quantity} {item}"
            draw_text(
                self.surface,
                self.fonts.small,
                ellipsize(self.fonts.small, text, slot_width - 12),
                PALETTE.text,
                (x, rect.y + 31),
            )
            draw_text(
                self.surface,
                self.fonts.tiny,
                f"{value:.2f} Credits",
                PALETTE.muted,
                (x, rect.y + 51),
            )

    def _draw_production(self, content: pygame.Rect) -> None:
        """Draw every recipe with effective costs and material status."""
        y = self._draw_page_heading(
            content,
            "WORKSHOP",
            "Production",
            "Review recipes, compare material requirements and manufacture goods.",
        )
        x = content.x + CONTENT_PADDING
        width = content.width - CONTENT_PADDING * 2
        viewport = pygame.Rect(x, y, width, content.bottom - y - 18)
        card_gap = 12
        card_height = 132
        card_width = (viewport.width - card_gap) // 2
        recipes = tuple(PRODUCTION_RECIPES.items())
        rows = (len(recipes) + 1) // 2
        total_height = rows * (card_height + card_gap) - card_gap
        self.max_scroll[View.PRODUCTION] = max(0, total_height - viewport.height)
        scroll = min(
            self.scroll_offsets[View.PRODUCTION],
            self.max_scroll[View.PRODUCTION],
        )
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        for index, (product, recipe) in enumerate(recipes):
            column = index % 2
            row_index = index // 2
            card = pygame.Rect(
                viewport.x + column * (card_width + card_gap),
                viewport.y + row_index * (card_height + card_gap) - scroll,
                card_width,
                card_height,
            )
            if card.bottom < viewport.top or card.top > viewport.bottom:
                continue
            draw_panel(self.surface, card)
            draw_text(
                self.surface,
                self.fonts.body_bold,
                product.display_name,
                PALETTE.text,
                (card.x + 14, card.y + 12),
            )
            effective_cost = self.engine.get_production_cost(product)
            draw_text(
                self.surface,
                self.fonts.small,
                f"{effective_cost:.2f} C",
                PALETTE.cyan,
                (card.right - 14, card.y + 13),
                anchor="topright",
            )
            materials = ", ".join(
                f"{amount} {material.display_name}"
                for material, amount in recipe.materials.items()
            )
            draw_text(
                self.surface,
                self.fonts.small,
                ellipsize(self.fonts.small, materials, card.width - 28),
                PALETTE.muted,
                (card.x + 14, card.y + 43),
            )
            missing = [
                material.display_name
                for material, amount in recipe.materials.items()
                if self.engine.player.stock.get(material, 0) < amount
            ]
            affordable = self.engine.player.money >= effective_cost
            available = not missing and affordable
            if missing:
                status = f"Missing: {', '.join(missing)}"
                status_color = PALETTE.amber
            elif not affordable:
                status = "Not enough Credits"
                status_color = PALETTE.red
            else:
                status = "Materials available"
                status_color = PALETTE.green
            draw_text(
                self.surface,
                self.fonts.tiny,
                ellipsize(self.fonts.tiny, status, card.width - 126),
                status_color,
                (card.x + 14, card.bottom - 32),
                anchor="midleft",
            )
            button_rect = pygame.Rect(card.right - 110, card.bottom - 47, 96, 34)
            visible = card.top >= viewport.top and card.bottom <= viewport.bottom
            self._button(
                button_rect,
                "Produce",
                "open_produce",
                product,
                primary=available,
                enabled=available,
                compact=True,
                register=visible,
            )
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, scroll)

    def _draw_fleet(self, content: pygame.Rect) -> None:
        """Draw owned ships or the complete ship model catalog."""
        y = self._draw_page_heading(
            content,
            "HANGAR",
            "Fleet & shipyard",
            "Manage owned ships or purchase models for new trade routes.",
        )
        x = content.x + CONTENT_PADDING
        width = content.width - CONTENT_PADDING * 2
        owned_rect = pygame.Rect(x, y, 120, 36)
        shop_rect = pygame.Rect(x + 128, y, 120, 36)
        self._button(
            owned_rect,
            "My fleet",
            "fleet_mode",
            FleetMode.OWNED,
            selected=self.fleet_mode is FleetMode.OWNED,
            compact=True,
        )
        self._button(
            shop_rect,
            "Shipyard",
            "fleet_mode",
            FleetMode.SHIPYARD,
            selected=self.fleet_mode is FleetMode.SHIPYARD,
            compact=True,
        )
        viewport = pygame.Rect(x, y + 48, width, content.bottom - y - 66)
        if self.fleet_mode is FleetMode.OWNED:
            self._draw_owned_fleet(viewport)
        else:
            self._draw_shipyard(viewport)

    def _draw_owned_fleet(self, viewport: pygame.Rect) -> None:
        """Draw each player-owned ship and its current mission."""
        ships = self.engine.fleet.ships
        if not ships:
            draw_panel(self.surface, viewport)
            draw_text(
                self.surface,
                self.fonts.heading,
                "No ships owned",
                PALETTE.text,
                (viewport.centerx, viewport.centery - 14),
                anchor="center",
            )
            draw_text(
                self.surface,
                self.fonts.small,
                "Open the shipyard to purchase your first transporter.",
                PALETTE.muted,
                (viewport.centerx, viewport.centery + 18),
                anchor="center",
            )
            self.max_scroll[View.FLEET] = 0
            return
        card_height = 126
        gap = 12
        total_height = len(ships) * (card_height + gap) - gap
        self.max_scroll[View.FLEET] = max(0, total_height - viewport.height)
        scroll = min(self.scroll_offsets[View.FLEET], self.max_scroll[View.FLEET])
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        for index, ship in enumerate(ships):
            card = pygame.Rect(
                viewport.x,
                viewport.y + index * (card_height + gap) - scroll,
                viewport.width,
                card_height,
            )
            if card.bottom < viewport.top or card.top > viewport.bottom:
                continue
            draw_panel(self.surface, card)
            badge_rect = pygame.Rect(card.x + 14, card.y + 14, 66, 66)
            pygame.draw.rect(
                self.surface, PALETTE.cyan_soft, badge_rect, border_radius=10
            )
            draw_text(
                self.surface,
                self.fonts.body_bold,
                f"#{ship.ship_id}",
                PALETTE.cyan,
                badge_rect.center,
                anchor="center",
            )
            body_x = badge_rect.right + 16
            draw_text(
                self.surface,
                self.fonts.body_bold,
                ship.model.display_name,
                PALETTE.text,
                (body_x, card.y + 14),
            )
            draw_text(
                self.surface,
                self.fonts.small,
                f"{ship.model.cargo_type} · Capacity {ship.model.cargo_capacity} · "
                f"Speed {ship.model.speed_rating} · Defense {ship.model.defense_rating}",
                PALETTE.muted,
                (body_x, card.y + 40),
            )
            if ship.active_transport is None:
                draw_text(
                    self.surface,
                    self.fonts.small,
                    "READY",
                    PALETTE.green,
                    (body_x, card.y + 74),
                )
            else:
                mission = ship.active_transport
                status = (
                    f"{mission.quantity} {mission.product.display_name} from "
                    f"{mission.product.planet.display_name} · "
                    f"{mission.remaining_rounds}/{mission.total_rounds} rounds left"
                )
                draw_text(
                    self.surface,
                    self.fonts.small,
                    ellipsize(self.fonts.small, status, card.width - body_x + card.x - 138),
                    PALETTE.amber,
                    (body_x, card.y + 69),
                )
                completed = 1 - mission.remaining_rounds / mission.total_rounds
                draw_progress(
                    self.surface,
                    pygame.Rect(body_x, card.y + 94, card.width - (body_x - card.x) - 138, 6),
                    completed,
                )
            button_rect = pygame.Rect(card.right - 112, card.centery - 18, 96, 36)
            visible = card.top >= viewport.top and card.bottom <= viewport.bottom
            self._button(
                button_rect,
                "Sell ship",
                "open_sell_ship",
                ship.ship_id,
                enabled=ship.is_available,
                compact=True,
                register=visible,
            )
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, scroll)

    def _draw_shipyard(self, viewport: pygame.Rect) -> None:
        """Draw all registered ship models and their effective prices."""
        models = get_all_ship_models()
        gap = 12
        card_height = 132
        card_width = (viewport.width - gap) // 2
        rows = (len(models) + 1) // 2
        total_height = rows * (card_height + gap) - gap
        self.max_scroll[View.FLEET] = max(0, total_height - viewport.height)
        scroll = min(self.scroll_offsets[View.FLEET], self.max_scroll[View.FLEET])
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        for index, model in enumerate(models):
            column = index % 2
            row_index = index // 2
            card = pygame.Rect(
                viewport.x + column * (card_width + gap),
                viewport.y + row_index * (card_height + gap) - scroll,
                card_width,
                card_height,
            )
            if card.bottom < viewport.top or card.top > viewport.bottom:
                continue
            draw_panel(self.surface, card)
            pygame.draw.rect(
                self.surface,
                self._cargo_color_from_name(model.cargo_type.name),
                pygame.Rect(card.x + 14, card.y + 15, 5, 31),
                border_radius=3,
            )
            draw_text(
                self.surface,
                self.fonts.body_bold,
                model.display_name,
                PALETTE.text,
                (card.x + 29, card.y + 12),
            )
            draw_text(
                self.surface,
                self.fonts.tiny,
                str(model.cargo_type).upper(),
                PALETTE.muted,
                (card.x + 29, card.y + 36),
            )
            spec_text = (
                f"Capacity {model.cargo_capacity}   Speed {model.speed_rating}   "
                f"Defense {model.defense_rating}"
            )
            draw_text(
                self.surface,
                self.fonts.small,
                spec_text,
                PALETTE.muted,
                (card.x + 14, card.y + 66),
            )
            price = self.engine.get_ship_purchase_price(model)
            draw_text(
                self.surface,
                self.fonts.body_bold,
                f"{price:.2f} C",
                PALETTE.text,
                (card.x + 14, card.bottom - 25),
                anchor="midleft",
            )
            affordable = self.engine.player.money >= price
            button_rect = pygame.Rect(card.right - 102, card.bottom - 43, 88, 32)
            visible = card.top >= viewport.top and card.bottom <= viewport.bottom
            self._button(
                button_rect,
                "Buy",
                "open_buy_ship",
                model,
                primary=affordable,
                enabled=affordable,
                compact=True,
                register=visible,
            )
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, scroll)

    def _draw_investments(self, content: pygame.Rect) -> None:
        """Draw permanent investments, prices, effects and ownership."""
        y = self._draw_page_heading(
            content,
            "BUSINESS DEVELOPMENT",
            "Investments",
            "Purchase permanent improvements for production and ship acquisition.",
        )
        x = content.x + CONTENT_PADDING
        width = content.width - CONTENT_PADDING * 2
        gap = 16
        card_width = (width - gap) // 2
        for index, investment in enumerate(Investment):
            card = pygame.Rect(x + index * (card_width + gap), y, card_width, 238)
            draw_panel(self.surface, card)
            icon_rect = pygame.Rect(card.x + 18, card.y + 18, 56, 56)
            pygame.draw.rect(
                self.surface, PALETTE.cyan_soft, icon_rect, border_radius=10
            )
            draw_text(
                self.surface,
                self.fonts.heading,
                "F" if investment is Investment.FACTORY else "S",
                PALETTE.cyan,
                icon_rect.center,
                anchor="center",
            )
            draw_text(
                self.surface,
                self.fonts.heading,
                investment.display_name,
                PALETTE.text,
                (icon_rect.right + 14, card.y + 20),
            )
            draw_text(
                self.surface,
                self.fonts.tiny,
                investment.investment_id.upper(),
                PALETTE.muted,
                (icon_rect.right + 14, card.y + 50),
            )
            description_rect = pygame.Rect(
                card.x + 18,
                card.y + 92,
                card.width - 36,
                48,
            )
            draw_wrapped_text(
                self.surface,
                self.fonts.small,
                investment.description,
                PALETTE.muted,
                description_rect,
                line_gap=2,
                max_lines=2,
            )
            owned = self.engine.investments.owns(investment)
            status = "PURCHASED" if owned else "AVAILABLE"
            draw_text(
                self.surface,
                self.fonts.small,
                status,
                PALETTE.green if owned else PALETTE.cyan,
                (card.x + 18, card.bottom - 65),
            )
            draw_text(
                self.surface,
                self.fonts.body_bold,
                f"{investment.purchase_price:,.2f} C",
                PALETTE.text,
                (card.x + 18, card.bottom - 32),
                anchor="midleft",
            )
            affordable = self.engine.player.money >= investment.purchase_price
            button_rect = pygame.Rect(card.right - 132, card.bottom - 50, 114, 36)
            self._button(
                button_rect,
                "Purchased" if owned else "Buy",
                "open_investment",
                investment,
                primary=affordable and not owned,
                enabled=affordable and not owned,
                compact=True,
            )
        self.max_scroll[View.INVESTMENTS] = 0

    def _draw_dialog(self, dialog: DialogState) -> None:
        """Draw the active modal and only modal hit targets."""
        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*PALETTE.overlay, 225))
        self.surface.blit(overlay, (0, 0))
        if dialog.kind is DialogKind.ROUND_REPORT:
            size = (620, min(540, self.surface.get_height() - 70))
        elif dialog.kind in {DialogKind.TRANSPORT, DialogKind.LOAD}:
            size = (520, min(510, self.surface.get_height() - 70))
        else:
            size = (500, 390 if dialog.kind is DialogKind.TRADE else 330)
        rect = pygame.Rect(0, 0, *size)
        rect.center = self.surface.get_rect().center
        draw_panel(self.surface, rect, color=PALETTE.panel, radius=14)

        if dialog.kind is DialogKind.TRADE:
            self._draw_trade_dialog(rect, dialog)
        elif dialog.kind is DialogKind.TRANSPORT:
            self._draw_transport_dialog(rect, dialog)
        elif dialog.kind is DialogKind.PRODUCE:
            self._draw_production_dialog(rect, dialog)
        elif dialog.kind is DialogKind.BUY_SHIP:
            self._draw_ship_dialog(rect, dialog, buying=True)
        elif dialog.kind is DialogKind.SELL_SHIP:
            self._draw_ship_dialog(rect, dialog, buying=False)
        elif dialog.kind is DialogKind.BUY_INVESTMENT:
            self._draw_investment_dialog(rect, dialog)
        elif dialog.kind is DialogKind.LOAD:
            self._draw_load_dialog(rect, dialog)
        elif dialog.kind is DialogKind.ROUND_REPORT:
            self._draw_round_report(rect, dialog)
        else:
            self._draw_quit_dialog(rect)

    def _draw_dialog_header(
        self,
        rect: pygame.Rect,
        eyebrow: str,
        title: str,
    ) -> int:
        """Draw a modal heading and close button, returning content y."""
        draw_text(
            self.surface,
            self.fonts.tiny,
            eyebrow,
            PALETTE.cyan,
            (rect.x + 22, rect.y + 19),
        )
        draw_text(
            self.surface,
            self.fonts.heading,
            title,
            PALETTE.text,
            (rect.x + 22, rect.y + 40),
        )
        self._button(
            pygame.Rect(rect.right - 54, rect.y + 18, 34, 34),
            "×",
            "close_dialog",
            modal=True,
            compact=True,
        )
        return rect.y + 86

    def _draw_trade_dialog(self, rect: pygame.Rect, dialog: DialogState) -> None:
        """Draw quantity controls for a market purchase or sale."""
        product = dialog.product
        if product is None:
            return
        buying = dialog.trade_action == "buy"
        y = self._draw_dialog_header(
            rect,
            "BUY GOODS" if buying else "SELL GOODS",
            product.display_name,
        )
        draw_text(
            self.surface,
            self.fonts.small,
            "Quantity",
            PALETTE.muted,
            (rect.x + 24, y),
        )
        stepper = pygame.Rect(rect.x + 24, y + 24, rect.width - 48, 46)
        minus = pygame.Rect(stepper.x, stepper.y, 46, stepper.height)
        plus = pygame.Rect(stepper.right - 46, stepper.y, 46, stepper.height)
        self._button(minus, "−", "adjust_quantity", -1, modal=True)
        self._button(plus, "+", "adjust_quantity", 1, modal=True)
        draw_panel(self.surface, pygame.Rect(minus.right, stepper.y, stepper.width - 92, 46), radius=0)
        draw_text(
            self.surface,
            self.fonts.body_bold,
            str(dialog.quantity),
            PALETTE.text,
            stepper.center,
            anchor="center",
        )
        unit_price = self.engine.markets[product].current_price
        total = unit_price * dialog.quantity
        self._draw_summary_line(rect, y + 92, "Unit price", f"{unit_price:.2f} C")
        self._draw_summary_line(rect, y + 126, "Total", f"{total:.2f} C")
        self._draw_dialog_message(rect, dialog.message, y + 161)
        self._draw_dialog_actions(
            rect,
            "Choose transport" if buying else "Confirm sale",
            "confirm_trade",
        )

    def _draw_transport_dialog(self, rect: pygame.Rect, dialog: DialogState) -> None:
        """Draw compatible ship choices for a pending product purchase."""
        product = dialog.product
        if product is None:
            return
        y = self._draw_dialog_header(rect, "SELECT TRANSPORT", product.display_name)
        draw_text(
            self.surface,
            self.fonts.small,
            f"{dialog.quantity} units · {product.cargo_type}",
            PALETTE.muted,
            (rect.x + 22, y),
        )
        viewport = pygame.Rect(rect.x + 22, y + 28, rect.width - 44, rect.height - 164)
        row_height = 64
        total_height = len(dialog.transport_options) * (row_height + 8)
        dialog.scroll = min(dialog.scroll, max(0, total_height - viewport.height))
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        for index, option in enumerate(dialog.transport_options):
            option_rect = pygame.Rect(
                viewport.x,
                viewport.y + index * (row_height + 8) - dialog.scroll,
                viewport.width,
                row_height,
            )
            if option_rect.bottom < viewport.top or option_rect.top > viewport.bottom:
                continue
            draw_panel(self.surface, option_rect, color=PALETTE.panel_alt, radius=8)
            draw_text(
                self.surface,
                self.fonts.body_bold,
                f"{option.ship_name} · #{option.ship_id}",
                PALETTE.text,
                (option_rect.x + 13, option_rect.y + 11),
            )
            draw_text(
                self.surface,
                self.fonts.small,
                f"Capacity {option.cargo_capacity} · Return in "
                f"{option.travel_rounds} round(s)",
                PALETTE.muted,
                (option_rect.x + 13, option_rect.y + 38),
            )
            visible = option_rect.top >= viewport.top and option_rect.bottom <= viewport.bottom
            self.hit_targets.append(
                HitTarget(
                    rect=option_rect.copy(),
                    action="choose_transport",
                    payload=option.ship_id,
                    modal=True,
                    enabled=visible,
                )
            )
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, dialog.scroll)
        self._button(
            pygame.Rect(rect.x + 22, rect.bottom - 54, 92, 34),
            "Back",
            "transport_back",
            modal=True,
            compact=True,
        )
        self._draw_dialog_message(rect, dialog.message, rect.bottom - 82)

    def _draw_production_dialog(self, rect: pygame.Rect, dialog: DialogState) -> None:
        """Draw production quantity, requirements and total cost."""
        product = dialog.product
        if product is None:
            return
        recipe = PRODUCTION_RECIPES[product]
        y = self._draw_dialog_header(rect, "PRODUCE GOODS", product.display_name)
        requirements = ", ".join(
            f"{amount * dialog.quantity} {material.display_name}"
            for material, amount in recipe.materials.items()
        )
        draw_text(
            self.surface,
            self.fonts.small,
            ellipsize(self.fonts.small, requirements, rect.width - 48),
            PALETTE.muted,
            (rect.x + 24, y),
        )
        stepper = pygame.Rect(rect.x + 24, y + 34, 170, 44)
        self._button(
            pygame.Rect(stepper.x, stepper.y, 44, 44),
            "−",
            "adjust_quantity",
            -1,
            modal=True,
        )
        self._button(
            pygame.Rect(stepper.right - 44, stepper.y, 44, 44),
            "+",
            "adjust_quantity",
            1,
            modal=True,
        )
        draw_text(
            self.surface,
            self.fonts.body_bold,
            str(dialog.quantity),
            PALETTE.text,
            stepper.center,
            anchor="center",
        )
        total = self.engine.get_production_cost(product, dialog.quantity)
        self._draw_summary_line(rect, y + 96, "Production cost", f"{total:.2f} C")
        self._draw_dialog_message(rect, dialog.message, y + 137)
        self._draw_dialog_actions(rect, "Produce", "confirm_produce")

    def _draw_ship_dialog(
        self,
        rect: pygame.Rect,
        dialog: DialogState,
        *,
        buying: bool,
    ) -> None:
        """Draw ship purchase or sale confirmation."""
        if buying:
            model = dialog.ship_model
            if model is None:
                return
            title = model.display_name
            price = self.engine.get_ship_purchase_price(model)
            description = (
                f"{model.cargo_type} · Capacity {model.cargo_capacity} · "
                f"Speed {model.speed_rating} · Defense {model.defense_rating}"
            )
            eyebrow = "BUY SPACESHIP"
            action = "confirm_buy_ship"
            action_label = f"Buy for {price:.2f} C"
        else:
            if dialog.ship_id is None:
                return
            try:
                ship = self.engine.fleet.get_ship(dialog.ship_id)
            except GameException as error:
                dialog.message = str(error)
                return
            title = ship.model.display_name
            price = round(ship.model.purchase_price * 0.70, 2)
            description = (
                f"Ship #{ship.ship_id} will be removed from your fleet. "
                "Ships in transit cannot be sold."
            )
            eyebrow = "SELL SPACESHIP"
            action = "confirm_sell_ship"
            action_label = f"Sell for {price:.2f} C"
        y = self._draw_dialog_header(rect, eyebrow, title)
        draw_wrapped_text(
            self.surface,
            self.fonts.small,
            description,
            PALETTE.muted,
            pygame.Rect(rect.x + 24, y, rect.width - 48, 65),
            line_gap=3,
            max_lines=3,
        )
        self._draw_dialog_message(rect, dialog.message, y + 86)
        self._draw_dialog_actions(rect, action_label, action)

    def _draw_investment_dialog(
        self,
        rect: pygame.Rect,
        dialog: DialogState,
    ) -> None:
        """Draw investment details and confirmation."""
        investment = dialog.investment
        if investment is None:
            return
        y = self._draw_dialog_header(rect, "BUY INVESTMENT", investment.display_name)
        draw_wrapped_text(
            self.surface,
            self.fonts.small,
            investment.description,
            PALETTE.muted,
            pygame.Rect(rect.x + 24, y, rect.width - 48, 55),
            line_gap=3,
            max_lines=2,
        )
        self._draw_summary_line(
            rect,
            y + 74,
            "Purchase price",
            f"{investment.purchase_price:,.2f} C",
        )
        self._draw_dialog_message(rect, dialog.message, y + 113)
        self._draw_dialog_actions(rect, "Buy investment", "confirm_investment")

    def _draw_load_dialog(self, rect: pygame.Rect, dialog: DialogState) -> None:
        """Draw available timestamped save games."""
        y = self._draw_dialog_header(rect, "SAVE GAMES", "Load game")
        viewport = pygame.Rect(rect.x + 22, y, rect.width - 44, rect.height - 151)
        if not dialog.save_paths:
            draw_text(
                self.surface,
                self.fonts.small,
                "No save games found.",
                PALETTE.muted,
                viewport.center,
                anchor="center",
            )
            return
        row_height = 52
        total_height = len(dialog.save_paths) * (row_height + 7)
        dialog.scroll = min(dialog.scroll, max(0, total_height - viewport.height))
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        for index, path in enumerate(dialog.save_paths):
            row = pygame.Rect(
                viewport.x,
                viewport.y + index * (row_height + 7) - dialog.scroll,
                viewport.width,
                row_height,
            )
            if row.bottom < viewport.top or row.top > viewport.bottom:
                continue
            draw_panel(self.surface, row, color=PALETTE.panel_alt, radius=8)
            draw_text(
                self.surface,
                self.fonts.small,
                path.stem,
                PALETTE.text,
                (row.x + 13, row.centery),
                anchor="midleft",
            )
            draw_text(
                self.surface,
                self.fonts.body,
                ">",
                PALETTE.cyan,
                (row.right - 15, row.centery),
                anchor="midright",
            )
            visible = row.top >= viewport.top and row.bottom <= viewport.bottom
            self.hit_targets.append(
                HitTarget(
                    rect=row.copy(),
                    action="choose_save",
                    payload=path,
                    enabled=visible,
                    modal=True,
                )
            )
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, dialog.scroll)
        self._draw_dialog_message(rect, dialog.message, rect.bottom - 57)

    def _draw_round_report(self, rect: pygame.Rect, dialog: DialogState) -> None:
        """Draw event, piracy and delivery outcomes from the completed round."""
        result = dialog.round_result
        if result is None:
            return
        y = self._draw_dialog_header(
            rect,
            "ROUND REPORT",
            f"Round {self.engine.round_number} begins",
        )
        messages: list[tuple[str, str]] = []
        if result.market_event is None:
            messages.append(("MARKET", "No market event occurred this round."))
        else:
            messages.append(("MARKET EVENT", result.market_event.message))
        if result.pirate_attack is not None:
            messages.append(("PIRATE ACTIVITY", result.pirate_attack.message))
        for delivery in result.completed_deliveries:
            messages.append(("DELIVERY", delivery.message))
        if result.pirate_attack is None and not result.completed_deliveries:
            messages.append(("OPERATIONS", "No piracy or deliveries to report."))

        viewport = pygame.Rect(rect.x + 22, y, rect.width - 44, rect.height - 158)
        item_heights: list[int] = []
        for _, message in messages:
            line_count = max(1, len(message) // 68 + 1)
            item_heights.append(46 + min(3, line_count) * 17)
        total_height = sum(item_heights) + max(0, len(item_heights) - 1) * 8
        dialog.scroll = min(dialog.scroll, max(0, total_height - viewport.height))
        previous_clip = self.surface.get_clip()
        self.surface.set_clip(viewport)
        cursor_y = viewport.y - dialog.scroll
        for (label, message), item_height in zip(messages, item_heights, strict=True):
            item = pygame.Rect(viewport.x, cursor_y, viewport.width, item_height)
            if item.bottom >= viewport.top and item.top <= viewport.bottom:
                draw_panel(self.surface, item, color=PALETTE.panel_alt, radius=8)
                draw_text(
                    self.surface,
                    self.fonts.tiny,
                    label,
                    PALETTE.cyan if label != "PIRATE ACTIVITY" else PALETTE.amber,
                    (item.x + 13, item.y + 11),
                )
                draw_wrapped_text(
                    self.surface,
                    self.fonts.small,
                    message,
                    PALETTE.text,
                    pygame.Rect(item.x + 13, item.y + 30, item.width - 26, item.height - 36),
                    line_gap=2,
                    max_lines=3,
                )
            cursor_y += item_height + 8
        self.surface.set_clip(previous_clip)
        self._draw_scrollbar(viewport, total_height, dialog.scroll)
        self._button(
            pygame.Rect(rect.right - 116, rect.bottom - 52, 94, 34),
            "Continue",
            "close_dialog",
            primary=True,
            modal=True,
            compact=True,
        )

    def _draw_quit_dialog(self, rect: pygame.Rect) -> None:
        """Draw the application exit confirmation."""
        y = self._draw_dialog_header(rect, "END SESSION", "Quit Galactic Trader?")
        draw_wrapped_text(
            self.surface,
            self.fonts.small,
            "Unsaved progress will be lost. You can cancel and save the game first.",
            PALETTE.muted,
            pygame.Rect(rect.x + 24, y, rect.width - 48, 60),
            line_gap=3,
            max_lines=3,
        )
        self._draw_dialog_actions(rect, "Quit game", "confirm_quit", destructive=True)

    def _draw_summary_line(
        self,
        rect: pygame.Rect,
        y: int,
        label: str,
        value: str,
    ) -> None:
        """Draw a label/value row inside a modal."""
        draw_text(
            self.surface,
            self.fonts.small,
            label,
            PALETTE.muted,
            (rect.x + 24, y),
        )
        draw_text(
            self.surface,
            self.fonts.small,
            value,
            PALETTE.text,
            (rect.right - 24, y),
            anchor="topright",
        )
        pygame.draw.line(
            self.surface,
            PALETTE.edge,
            (rect.x + 24, y + 25),
            (rect.right - 24, y + 25),
        )

    def _draw_dialog_message(self, rect: pygame.Rect, message: str, y: int) -> None:
        """Draw an inline validation error when one exists."""
        if not message:
            return
        draw_text(
            self.surface,
            self.fonts.small,
            ellipsize(self.fonts.small, message, rect.width - 48),
            PALETTE.red,
            (rect.x + 24, y),
        )

    def _draw_dialog_actions(
        self,
        rect: pygame.Rect,
        primary_label: str,
        primary_action: str,
        *,
        destructive: bool = False,
    ) -> None:
        """Draw standard cancel and confirmation controls."""
        y = rect.bottom - 56
        self._button(
            pygame.Rect(rect.right - 222, y, 90, 36),
            "Cancel",
            "close_dialog",
            modal=True,
            compact=True,
        )
        primary_rect = pygame.Rect(rect.right - 124, y, 104, 36)
        if destructive:
            pygame.draw.rect(self.surface, PALETTE.red, primary_rect, border_radius=7)
            draw_text(
                self.surface,
                self.fonts.small,
                primary_label,
                PALETTE.deep,
                primary_rect.center,
                anchor="center",
            )
            self.hit_targets.append(
                HitTarget(primary_rect, primary_action, modal=True)
            )
        else:
            self._button(
                primary_rect,
                primary_label,
                primary_action,
                primary=True,
                modal=True,
                compact=True,
            )

    def _draw_toast(self, toast: Toast) -> None:
        """Draw a non-blocking success or error notification."""
        width = min(440, self.surface.get_width() - 40)
        rect = pygame.Rect(
            self.surface.get_width() - width - 20,
            self.surface.get_height() - 82,
            width,
            58,
        )
        draw_panel(
            self.surface,
            rect,
            color=PALETTE.panel,
            border_color=PALETTE.red if toast.is_error else PALETTE.cyan_dark,
            radius=9,
        )
        pygame.draw.rect(
            self.surface,
            PALETTE.red if toast.is_error else PALETTE.cyan,
            pygame.Rect(rect.x, rect.y, 4, rect.height),
            border_radius=2,
        )
        draw_text(
            self.surface,
            self.fonts.small,
            ellipsize(self.fonts.small, toast.message, rect.width - 30),
            PALETTE.text,
            (rect.x + 16, rect.centery),
            anchor="midleft",
        )

    def _draw_scrollbar(
        self,
        viewport: pygame.Rect,
        content_height: int,
        offset: int,
    ) -> None:
        """Draw a subtle scrollbar when the content exceeds its viewport."""
        if content_height <= viewport.height or viewport.height <= 0:
            return
        track = pygame.Rect(viewport.right - 4, viewport.y + 3, 2, viewport.height - 6)
        pygame.draw.rect(self.surface, PALETTE.edge, track, border_radius=1)
        thumb_height = max(24, round(track.height * viewport.height / content_height))
        max_offset = content_height - viewport.height
        thumb_y = track.y + round((track.height - thumb_height) * offset / max_offset)
        pygame.draw.rect(
            self.surface,
            PALETTE.cyan_dark,
            pygame.Rect(track.x - 1, thumb_y, 4, thumb_height),
            border_radius=2,
        )

    def _button(
        self,
        rect: pygame.Rect,
        label: str,
        action: str,
        payload: object | None = None,
        *,
        primary: bool = False,
        selected: bool = False,
        enabled: bool = True,
        compact: bool = False,
        modal: bool = False,
        register: bool = True,
    ) -> None:
        """Draw a button and optionally register its current hit target."""
        draw_button(
            self.surface,
            self.fonts,
            rect,
            label,
            primary=primary,
            selected=selected,
            enabled=enabled,
            compact=compact,
        )
        if register:
            self.hit_targets.append(
                HitTarget(
                    rect=rect.copy(),
                    action=action,
                    payload=payload,
                    enabled=enabled,
                    modal=modal,
                )
            )

    @staticmethod
    def _cargo_color(product: Product) -> tuple[int, int, int]:
        """Return the stable accent color for a product's cargo type."""
        return PygameUI._cargo_color_from_name(product.cargo_type.name)

    @staticmethod
    def _cargo_color_from_name(name: str) -> tuple[int, int, int]:
        """Return the stable accent color for a cargo type name."""
        colors = {
            "STANDARD": PALETTE.green,
            "LIQUID": PALETTE.amber,
            "REFRIGERATED": PALETTE.cyan,
            "HAZARDOUS": PALETTE.red,
        }
        return colors.get(name, PALETTE.muted)
