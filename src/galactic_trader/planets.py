"""Planet definitions and their immutable travel information."""

from dataclasses import dataclass
from enum import Enum, unique


@dataclass(frozen=True)
class PlanetInfo:
    """Describes the fixed properties of a planet."""

    display_name: str
    description: str
    distance: int

    def __post_init__(self) -> None:
        """Validate the planet information."""
        if not self.display_name.strip():
            raise ValueError("Planet display name must not be empty.")
        if not self.description.strip():
            raise ValueError("Planet description must not be empty.")
        if self.distance <= 0:
            raise ValueError("Planet distance must be greater than zero.")


@unique
class Planet(Enum):
    """Contain all planets and their fixed information."""

    ENDOR = PlanetInfo(
        display_name="Endor",
        description="A sparsely populated planet covered in a dense forest.",
        distance=10,
    )
    ALDERAAN = PlanetInfo(
        display_name="Alderaan",
        description="A fertile agricultural world especially known for its expensive wines.",
        distance=35,
    )
    KESSEL = PlanetInfo(
        display_name="Kessel",
        description="An industrial mining planet rich in metallic ores but with harsh living conditions.",
        distance=60,
    )
    ABAFAR = PlanetInfo(
        display_name="Abafar",
        description="A desert world dominated by oil refineries.",
        distance=75,
    )
    KAMINO = PlanetInfo(
        display_name="Kamino",
        description="A cold research world known for its outstanding scientists and medical laboratories.",
        distance=80,
    )
    CORUSCANT = PlanetInfo(
        display_name="Coruscant",
        description="A wealthy planet famous for its luxury goods. It is located in the galaxy's central region.",
        distance=100,
    )
    KUAT = PlanetInfo(
        display_name="Kuat",
        description="A densely automated center of advanced manufacturing. Known for its excellent shipyards.",
        distance=125,
    )
    GEONOSIS = PlanetInfo(
        display_name="Geonosis",
        description="A remote world with guarded factories.",
        distance=150,
    )

    @property
    def display_name(self) -> str:
        """Return the planet's display name."""
        return self.value.display_name

    @property
    def description(self) -> str:
        """Return the planet's description."""
        return self.value.description

    @property
    def distance(self) -> int:
        """Return the one-way distance to the planet."""
        return self.value.distance

    def __str__(self) -> str:
        """Return the user-facing planet name."""
        return self.display_name
