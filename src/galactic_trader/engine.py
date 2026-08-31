"""Coordinates markets, player actions and round progression."""

from collections.abc import Iterator
from itertools import cycle
from random import Random
from typing import Final

from galactic_trader.events import (
    DEFAULT_EVENT_PROBABILITY,
    EventOccurrence,
    choose_market_event,
)
from galactic_trader.exceptions import NotEnoughMoneyException, NotProducibleException
from galactic_trader.fleet import Fleet, OwnedShip
from galactic_trader.inventory import Inventory
from galactic_trader.market import Market
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product
from galactic_trader.ships import get_ship_model

TREND_MULTIPLIER_MIN: Final[float] = 0.90
TREND_MULTIPLIER_MAX: Final[float] = 1.10
SHIP_RESALE_RATE: Final[float] = 0.70


class EconomyEngine:
    """Coordinates the mutable state and rules of the simulation."""

    def __init__(
        self,
        *,
        random_seed: int | None = None,
        event_probability: float = DEFAULT_EVENT_PROBABILITY,
    ) -> None:
        """Initializes engine state."""
        if not 0 <= event_probability <= 1:
            raise ValueError("Event probability must be between zero and one.")

        self._random = Random(random_seed)

        self.player = Inventory(money=100.0)
        self.fleet = Fleet()
        self.markets: dict[Product, Market] = {
            product: Market(
                product=product,
                current_price=product.starting_price,
                volatility=product.starting_volatility,
            )
            for product in Product
        }
        self._market_trends: Iterator[float] = cycle([0.2, 0.2, -0.1, -0.3])
        self.current_market_trend = next(self._market_trends)
        self.last_trend_multiplier = 1.0
        self.last_effective_market_trend = self.current_market_trend

        self.pending_price_directions: dict[Product, int] = {
            product: 0 for product in Product
        }
        self.history: list[tuple[str, str, int, float]] = []

        self.event_probability = event_probability
        self.last_market_event: EventOccurrence | None = None

    def interact_with_market(
        self, is_buy: bool, product: Product, quantity: int
    ) -> tuple[str, float]:
        """
        Executes the trade logic.
        Returns details of the transaction (Action Name, Transaction Price)
        or raises an exception.
        """
        assert quantity > 0

        market = self.markets[product]
        transaction_price = market.current_price
        # Buying -> positive quantity, Selling -> negative quantity
        signed_qty = quantity if is_buy else -quantity

        # 1. Execute logic (Raises exceptions if invalid)
        self.player.execute_trade(market.product, signed_qty, transaction_price)

        # 2. Update History
        action_name = "BUY" if is_buy else "SELL"
        self.history.append((action_name, str(product), quantity, transaction_price))

        # 3. Update Market Price (Supply/Demand)
        # +1 direction for Buy, -1 for Sell
        direction = 1 if is_buy else -1
        self.pending_price_directions[product] += direction * quantity

        return action_name, transaction_price

    def produce_product(self, product: Product, quantity: int) -> tuple[str, float]:
        """
        Produces a product if the product has a recipe.
        Return Action name and sum of cost or throws an exception.
        """
        assert quantity > 0

        recipe = PRODUCTION_RECIPES.get(product)

        if recipe is None:
            raise NotProducibleException(f"{product} cannot be produced.")

        total_cost = self.player.execute_production(
            product=product,
            quantity=quantity,
            recipe=recipe,
        )

        action_name = "PRODUCE"
        self.history.append((action_name, str(product), quantity, total_cost))

        return action_name, total_cost

    def buy_ship(self, model_id: str) -> tuple[OwnedShip, float]:
        """Buy one spaceship and return it with its purchase price."""
        model = get_ship_model(model_id)
        purchase_price = model.purchase_price

        if self.player.money < purchase_price:
            raise NotEnoughMoneyException(
                f"Need {purchase_price:.2f} Credits, "
                f"have {self.player.money:.2f} Credits."
            )

        self.player.money -= purchase_price
        purchased_ship = self.fleet.add_ship(model)
        self.history.append(
            (
                "BUY_SHIP",
                str(purchased_ship),
                purchase_price,
            )
        )
        return purchased_ship, purchase_price

    def sell_ship(self, ship_id: int) -> tuple[OwnedShip, float]:
        """Sell one owned spaceship for a fixed share of its purchase price."""
        owned_ship = self.fleet.get_ship(ship_id)
        sale_price = round(
            owned_ship.model.purchase_price * SHIP_RESALE_RATE,
            2,
        )

        self.fleet.remove_ship(ship_id)
        self.player.money += sale_price
        self.history.append(
            (
                "SELL_SHIP",
                str(owned_ship),
                sale_price,
            )
        )
        return owned_ship, sale_price

    def tick(self) -> EventOccurrence | None:
        """Advances the simulation by one round and applies all pending price changes."""
        self.last_trend_multiplier = self._random.uniform(
            TREND_MULTIPLIER_MIN, TREND_MULTIPLIER_MAX
        )
        self.last_effective_market_trend = (
            self.current_market_trend * self.last_trend_multiplier
        )

        for product, market in self.markets.items():
            direction = self.pending_price_directions[product]
            market.adjust_price(direction)
            market.set_price(market.current_price + self.last_effective_market_trend)
            self.pending_price_directions[product] = 0

        selected_event = choose_market_event(self._random, self.event_probability)
        if selected_event is None:
            self.last_market_event = None
        else:
            self.last_market_event = selected_event.apply(self.markets, self._random)

        self.current_market_trend = next(self._market_trends)

        return self.last_market_event
