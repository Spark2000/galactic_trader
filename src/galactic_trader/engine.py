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
        self.market_trend = cycle([0.2, 0.2, -0.1, -0.3])

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
        market.adjust_price(direction)

        return action_name, transaction_price

    def tick(self):
        """Advances the simulation by one step (Background market forces)."""
        trend = next(self.market_trend)
        for market in self.markets.values():
            market.set_price(market.current_price + trend)
