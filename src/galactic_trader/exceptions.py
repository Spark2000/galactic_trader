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


class UnknownShipModelException(GameException):
    """Report that no spaceship model has the requested model ID."""


class ShipNotOwnedException(GameException):
    """Report that the player does not own the requested spaceship."""


class ShipInTransitException(GameException):
    """Report that a spaceship is already performing a transport."""


class IncompatibleCargoException(GameException):
    """Report that a spaceship cannot carry the requested cargo type."""


class NotEnoughCargoCapacityException(GameException):
    """Report that a spaceship cannot hold the requested quantity."""


class UnknownInvestmentException(GameException):
    """Report that no investment has the requested identifier."""


class InvestmentAlreadyOwnedException(GameException):
    """Report that an investment has already been purchased."""


class SaveGameException(GameException):
    """Base class for errors while saving or loading a game."""


class InvalidSaveGameException(SaveGameException):
    """Report malformed or inconsistent save-game data."""


class UnsupportedSaveVersionException(SaveGameException):
    """Report a save game whose schema version is not supported."""


class SaveGameNotFoundException(SaveGameException):
    """Report that the requested save game does not exist."""
