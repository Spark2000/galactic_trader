"""Cargo types shared by products and spaceship models."""

from enum import Enum


class CargoType(Enum):
    """Describe the cargo hold required for a product."""

    STANDARD = "Standard cargo"
    LIQUID = "Liquid cargo"
    REFRIGERATED = "Refrigerated cargo"
    HAZARDOUS = "Hazardous cargo"

    def __str__(self) -> str:
        """Return the user-facing cargo type name."""
        return self.value