class GameException(Exception):
    """Base class for all game-related errors."""


class NotEnoughMoneyException(GameException):
    pass


class NotEnoughStockException(GameException):
    pass
