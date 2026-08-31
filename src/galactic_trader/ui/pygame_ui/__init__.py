"""pygame-ce user interface for Galactic Trader."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from galactic_trader.ui.pygame_ui.app import PygameUI

__all__ = ["PygameUI"]


def __getattr__(name: str) -> Any:
    """Import pygame and the graphical UI only when it is requested."""
    if name == "PygameUI":
        from galactic_trader.ui.pygame_ui.app import PygameUI

        return PygameUI
    raise AttributeError(name)
