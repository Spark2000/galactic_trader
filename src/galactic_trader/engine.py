from itertools import cycle

from galactic_trader.inventory import Inventory
from galactic_trader.market import Market
from galactic_trader.products import Product


class EconomyEngine:
    def __init__(self) -> None:
        """Initialize state."""
        self.player = Inventory(money=100.0)
        self.markets: dict[Product, Market] = {
            product: Market(
                product=product,
                current_price=product.starting_price,
                volatility=product.starting_volatility,
            )
            for product in Product
        }
        self.history: list[tuple] = []
        self.market_trends = cycle([0.2, 0.2, -0.1, -0.3])
        self.current_market_trend = next(self.market_trends)
        self.pending_price_directions: dict[Product, int] = {
            product: 0 for product in Product
        }

    def interact_with_market(
        self, is_buy: bool, product: Product, quantity: int
    ) -> tuple[str, float]:
        """
        Executes the trade logic.
        Returns details of the transaction (Action Name, Total Price)
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

    def tick(self):
        """Advances the simulation by one round and applies all pending price changes."""
        trend = self.current_market_trend
        # TODO add random value to trend

        for product, market in self.markets.items():
            direction = self.pending_price_directions[product]
            market.adjust_price(direction)
            market.set_price(market.current_price + trend)
            self.pending_price_directions[product] = 0

        self.current_market_trend = next(self.market_trends)
