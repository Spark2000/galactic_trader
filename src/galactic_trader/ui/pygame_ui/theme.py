"""Colors, measurements and fonts used by the pygame-ce interface."""

from dataclasses import dataclass
from typing import Final

import pygame

Color = tuple[int, int, int]

WINDOW_SIZE: Final[tuple[int, int]] = (1280, 720)
MIN_WINDOW_SIZE: Final[tuple[int, int]] = (960, 600)
TOP_BAR_HEIGHT: Final[int] = 72
SIDEBAR_WIDTH: Final[int] = 190


@dataclass(frozen=True)
class Palette:
    """Immutable color palette for the command-deck theme."""

    space: Color = (7, 17, 28)
    deep: Color = (11, 24, 37)
    panel: Color = (16, 33, 49)
    panel_alt: Color = (20, 42, 59)
    edge: Color = (40, 66, 86)
    text: Color = (232, 243, 248)
    muted: Color = (145, 168, 183)
    cyan: Color = (100, 230, 244)
    cyan_dark: Color = (48, 188, 204)
    cyan_soft: Color = (20, 57, 68)
    amber: Color = (255, 189, 98)
    green: Color = (101, 223, 156)
    red: Color = (255, 137, 137)
    overlay: Color = (3, 10, 17)


PALETTE: Final[Palette] = Palette()


@dataclass(frozen=True)
class Fonts:
    """Font sizes used throughout the interface."""

    title: pygame.font.Font
    heading: pygame.font.Font
    body: pygame.font.Font
    body_bold: pygame.font.Font
    small: pygame.font.Font
    tiny: pygame.font.Font


def create_fonts() -> Fonts:
    """Create a compact system-font hierarchy after pygame is initialized."""
    regular_name = pygame.font.match_font("avenirnext,arial,dejavusans")
    bold_name = pygame.font.match_font(
        "avenirnextdemibold,arialbold,dejavusansbold"
    )
    return Fonts(
        title=pygame.font.Font(bold_name, 34),
        heading=pygame.font.Font(bold_name, 21),
        body=pygame.font.Font(regular_name, 16),
        body_bold=pygame.font.Font(bold_name, 16),
        small=pygame.font.Font(regular_name, 13),
        tiny=pygame.font.Font(regular_name, 11),
    )
