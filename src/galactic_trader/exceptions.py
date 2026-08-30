"""Game-specifc exceptions raised by Galactic Trader."""


class GameException(Exception):
    """Base class for all game-related errors."""


class NotEnoughMoneyException(GameException):
    """error in case a transaction fails because player does not have enough money"""


class NotEnoughStockException(GameException):
    """error in case a transaction fails because player does not have enough stock"""
