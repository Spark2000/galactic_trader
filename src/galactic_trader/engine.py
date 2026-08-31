"""Coordinates markets, player actions, transports and round progression."""

from dataclasses import dataclass
from random import Random
from typing import Final

from galactic_trader.events import (
    DEFAULT_EVENT_PROBABILITY,
    EventOccurrence,
    choose_market_event,
)
from galactic_trader.events_transport import (
    DEFAULT_PIRATE_ATTACK_PROBABILITY,
    PirateAttackOccurrence,
    resolve_pirate_attack,
)
from galactic_trader.exceptions import (
    IncompatibleCargoException,
    InvestmentAlreadyOwnedException,
    NotEnoughCargoCapacityException,
    NotEnoughMoneyException,
    NotProducibleException,
    ShipInTransitException,
)
from galactic_trader.fleet import Fleet, OwnedShip
from galactic_trader.inventory import Inventory
from galactic_trader.investments import (
    Investment,
    InvestmentModifier,
    InvestmentPortfolio,
)
from galactic_trader.market import Market
from galactic_trader.production import PRODUCTION_RECIPES
from galactic_trader.products import Product
from galactic_trader.ships import ShipModel, get_ship_model
from galactic_trader.transport import (
    CompletedDelivery,
    ProductPurchase,
    TransportMission,
    TransportOption,
)

TREND_MULTIPLIER_MIN: Final[float] = 0.90
TREND_MULTIPLIER_MAX: Final[float] = 1.10
SHIP_RESALE_RATE: Final[float] = 0.70
MARKET_TRENDS: Final[tuple[float, ...]] = (0.2, 0.2, -0.1, -0.3)


@dataclass(frozen=True)
class RoundResult:
    """Contains the market event and deliveries completed during one tick."""

    market_event: EventOccurrence | None
    completed_deliveries: tuple[CompletedDelivery, ...]
    pirate_attack: PirateAttackOccurrence | None = None


class EconomyEngine:
    """Coordinates the mutable state and rules of the simulation."""

    def __init__(
        self,
        *,
        random_seed: int | None = None,
        event_probability: float = DEFAULT_EVENT_PROBABILITY,
        pirate_attack_probability: float = DEFAULT_PIRATE_ATTACK_PROBABILITY,
    ) -> None:
        """Initializes engine state."""
        if not 0 <= event_probability <= 1:
            raise ValueError("Event probability must be between zero and one.")
        if not 0 <= pirate_attack_probability <= 1:
            raise ValueError("Pirate attack probability must be between zero and one.")

        self._random = Random(random_seed)
        self.round_number = 1

        self.player = Inventory(money=100.0)
        self.fleet = Fleet()
        self.investments = InvestmentPortfolio()
        self.markets: dict[Product, Market] = {
            product: Market(
                product=product,
                current_price=product.starting_price,
                volatility=product.starting_volatility,
            )
            for product in Product
        }
        self._market_trend_index = 0
        self.current_market_trend = MARKET_TRENDS[self._market_trend_index]
        self.last_trend_multiplier = 1.0
        self.last_effective_market_trend = self.current_market_trend

        self.pending_price_directions: dict[Product, int] = {
            product: 0 for product in Product
        }
        self.history: list[tuple[str, str, int, float]] = []

        self.event_probability = event_probability
        self.last_market_event: EventOccurrence | None = None
        self.pirate_attack_probability = pirate_attack_probability
        self.last_pirate_attack: PirateAttackOccurrence | None = None

    @property
    def market_trend_index(self) -> int:
        """Returns the position of the trend used by the next round."""
        return self._market_trend_index

    def restore_round_state(
        self,
        *,
        round_number: int,
        market_trend_index: int,
        last_trend_multiplier: float,
        last_effective_market_trend: float,
    ) -> None:
        """Restores validated round and trend values from a save game."""
        if round_number <= 0:
            raise ValueError("Round number must be greater than zero.")
        if not 0 <= market_trend_index < len(MARKET_TRENDS):
            raise ValueError("Market trend index is outside the trend sequence.")
        if last_trend_multiplier <= 0:
            raise ValueError("Last trend multiplier must be greater than zero.")

        self.round_number = round_number
        self._market_trend_index = market_trend_index
        self.current_market_trend = MARKET_TRENDS[market_trend_index]
        self.last_trend_multiplier = last_trend_multiplier
        self.last_effective_market_trend = last_effective_market_trend

    def get_transport_options(
        self, product: Product, quantity: int
    ) -> tuple[TransportOption, ...]:
        """Returns all ships able to collect a planned product purchase."""
        available_ships = self.fleet.get_available_ships(product, quantity)
        return tuple(
            TransportOption(
                ship_id=ship.ship_id,
                ship_name=ship.model.display_name,
                cargo_capacity=ship.model.cargo_capacity,
                travel_rounds=ship.model.calculate_travel_rounds_to(product.planet),
            )
            for ship in available_ships
        )

    def buy_product(
        self, product: Product, quantity: int, ship_id: int
    ) -> ProductPurchase:
        """Buys products and starts their collection with an owned ship."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        ship = self.fleet.get_ship(ship_id)
        self._validate_transport_ship(ship, product, quantity)

        unit_price = self.markets[product].current_price
        total_cost = round(unit_price * quantity, 2)
        if self.player.money < total_cost:
            raise NotEnoughMoneyException(
                f"Need {total_cost:.2f} Credits, have {self.player.money:.2f} Credits."
            )

        travel_rounds = ship.model.calculate_travel_rounds_to(product.planet)
        mission = TransportMission(
            product=product,
            quantity=quantity,
            total_rounds=travel_rounds,
            remaining_rounds=travel_rounds,
        )

        ship.start_transport(mission)
        self.player.pay(total_cost)
        self.pending_price_directions[product] += quantity
        self.history.append(("BUY", str(product), quantity, unit_price))

        return ProductPurchase(
            product=product,
            quantity=quantity,
            ship_id=ship.ship_id,
            ship_name=ship.model.display_name,
            unit_price=unit_price,
            total_cost=total_cost,
            travel_rounds=travel_rounds,
        )

    @staticmethod
    def _validate_transport_ship(
        ship: OwnedShip, product: Product, quantity: int
    ) -> None:
        """Validates a selected ship without changing game state."""
        if not ship.is_available:
            raise ShipInTransitException(f"{ship} is already in transit.")
        if not ship.model.can_transport(product):
            raise IncompatibleCargoException(
                f"{ship} carries {ship.model.cargo_type}, "
                f"but {product} requires {product.cargo_type}."
            )
        if ship.model.cargo_capacity < quantity:
            raise NotEnoughCargoCapacityException(
                f"{ship} has capacity {ship.model.cargo_capacity}, "
                f"but the purchase contains {quantity} units."
            )

    def sell_product(self, product: Product, quantity: int) -> tuple[str, float]:
        """Sells stocked products immediately and queues their market effect."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        unit_price = self.markets[product].current_price
        self.player.execute_sale(product, quantity, unit_price)
        self.pending_price_directions[product] -= quantity
        self.history.append(("SELL", str(product), quantity, unit_price))
        return "SELL", unit_price

    def interact_with_market(
        self,
        is_buy: bool,
        product: Product,
        quantity: int,
        *,
        ship_id: int | None = None,
    ) -> tuple[str, float]:
        """Provides compatibility while routing trades through the new methods."""
        if is_buy:
            if ship_id is None:
                raise ValueError("Buying products requires a spaceship ID.")
            purchase = self.buy_product(product, quantity, ship_id)
            return "BUY", purchase.unit_price
        return self.sell_product(product, quantity)

    def produce_product(self, product: Product, quantity: int) -> tuple[str, float]:
        """
        Produces a product if the product has a recipe.
        Return Action name and sum of cost or throws an exception.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        recipe = PRODUCTION_RECIPES.get(product)

        if recipe is None:
            raise NotProducibleException(f"{product} cannot be produced.")

        total_cost = self.player.execute_production(
            product=product,
            quantity=quantity,
            recipe=recipe,
            cost_multiplier=self.investments.get_multiplier(
                InvestmentModifier.PRODUCTION_COST
            ),
        )

        action_name = "PRODUCE"
        self.history.append((action_name, str(product), quantity, total_cost))

        return action_name, total_cost

    def get_production_cost(self, product: Product, quantity: int = 1) -> float:
        """Returns the effective production cost for a product quantity."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        recipe = PRODUCTION_RECIPES.get(product)
        if recipe is None:
            raise NotProducibleException(f"{product} cannot be produced.")

        multiplier = self.investments.get_multiplier(InvestmentModifier.PRODUCTION_COST)
        return round(recipe.calculate_total_cost(quantity) * multiplier, 2)

    def get_ship_purchase_price(self, model: ShipModel) -> float:
        """Returns the effective purchase price of a spaceship model."""
        multiplier = self.investments.get_multiplier(
            InvestmentModifier.SHIP_PURCHASE_PRICE
        )
        return round(model.purchase_price * multiplier, 2)

    def buy_investment(
        self,
        investment: Investment,
    ) -> tuple[Investment, float]:
        """Purchases one permanent investment exactly once."""
        if self.investments.owns(investment):
            raise InvestmentAlreadyOwnedException(
                f"{investment} has already been purchased."
            )

        purchase_price = investment.purchase_price
        self.player.pay(purchase_price)
        self.investments.add(investment)
        self.history.append(("BUY_INVESTMENT", str(investment), 1, purchase_price))
        return investment, purchase_price

    def buy_ship(self, model_id: str) -> tuple[OwnedShip, float]:
        """Buy one spaceship and return it with its purchase price."""
        model = get_ship_model(model_id)
        purchase_price = self.get_ship_purchase_price(model)

        self.player.pay(purchase_price)
        purchased_ship = self.fleet.add_ship(model)
        self.history.append(
            (
                "BUY_SHIP",
                str(purchased_ship),
                1,
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
        self.player.credit(sale_price)
        self.history.append(
            (
                "SELL_SHIP",
                str(owned_ship),
                1,
                sale_price,
            )
        )
        return owned_ship, sale_price

    def tick(self) -> RoundResult:
        """Advance one round and apply prices, events, and transports."""
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

        self.last_pirate_attack = resolve_pirate_attack(
            fleet=self.fleet,
            random_generator=self._random,
            probability=self.pirate_attack_probability,
        )

        completed_deliveries: list[CompletedDelivery] = []
        for ship in self.fleet.ships:
            completed_transport = ship.advance_transport()
            if completed_transport is None:
                continue

            if completed_transport.quantity > 0:
                self.player.adjust_stock(
                    completed_transport.product,
                    completed_transport.quantity,
                )
            completed_deliveries.append(
                CompletedDelivery(
                    ship_id=ship.ship_id,
                    ship_name=ship.model.display_name,
                    product=completed_transport.product,
                    quantity=completed_transport.quantity,
                )
            )

        self._market_trend_index = (self._market_trend_index + 1) % len(MARKET_TRENDS)
        self.current_market_trend = MARKET_TRENDS[self._market_trend_index]
        self.round_number += 1

        return RoundResult(
            market_event=self.last_market_event,
            completed_deliveries=tuple(completed_deliveries),
            pirate_attack=self.last_pirate_attack,
        )
