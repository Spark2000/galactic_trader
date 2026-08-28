from itertools import cycle

from galactic_trader.inventory import Inventory
from galactic_trader.market import Market
from galactic_trader.products import Product


class EconomyEngine:
    def __init__(self):
        # 1. Initialize State
        self.player = Inventory(money=100.0)
        self.food_market = Market(
            product=Product.FOOD, current_price=10.0, volatility=0.5
        )
        self.history: list[tuple] = []
        self.market_trend = cycle([0.2, 0.2, -0.1, -0.3])

    def interact_with_market(self, is_buy: bool, quantity: int) -> tuple[str, float]:
        """
        Executes the trade logic.
        Returns details of the transaction (Action Name, Total Price)
        or raises an exception.
        """
        market = self.food_market
        # Math: Buy is positive quantity, Sell is negative
        signed_qty = quantity if is_buy else -quantity

        # 1. Execute logic (Raises exceptions if invalid)
        self.player.execute_trade(market.product, signed_qty, market.current_price)

        # 2. Update History
        action_name = "BUY" if is_buy else "SELL"
        self.history.append((action_name, quantity, market.current_price))

        # 3. Update Market Price (Supply/Demand)
        # +1 direction for Buy, -1 for Sell
        direction = 1 if is_buy else -1
        market.adjust_price(direction)

        return action_name, market.current_price

    def tick(self):
        """Advances the simulation by one step (Background market forces)."""
        trend = next(self.market_trend)
        new_price = self.food_market.current_price + trend
        self.food_market.current_price = max(1.0, round(new_price, 2))
