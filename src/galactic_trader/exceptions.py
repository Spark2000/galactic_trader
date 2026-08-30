"""Game-specifc exceptions raised by Galactic Trader."""


class GameException(Exception):
    """Base class for all game-related errors."""


class NotEnoughMoneyException(GameException):
    """Report that the player has not enough money to perform an action."""


class NotEnoughStockException(GameException):
    """Report that the player has not enough stock to perform an action."""


class NotEnoughMaterialsException(NotEnoughStockException):
    """Report that materials required for production are unavailable."""


class NotProducibleException(GameException):
    """Report that no production recipe exists for a product."""
