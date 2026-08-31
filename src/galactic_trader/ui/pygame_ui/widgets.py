"""Small drawing and hit-testing helpers for the pygame-ce UI."""

from dataclasses import dataclass

import pygame

from galactic_trader.ui.pygame_ui.theme import PALETTE, Color, Fonts

type Payload = object | None


@dataclass(frozen=True)
class HitTarget:
    """Describe one clickable region drawn during the current frame."""

    rect: pygame.Rect
    action: str
    payload: Payload = None
    enabled: bool = True
    modal: bool = False


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: Color,
    position: tuple[int, int],
    *,
    anchor: str = "topleft",
) -> pygame.Rect:
    """Render one text label using a pygame rectangle anchor."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    setattr(rect, anchor, position)
    surface.blit(rendered, rect)
    return rect


def ellipsize(font: pygame.font.Font, text: str, max_width: int) -> str:
    """Shorten text so it fits in the requested pixel width."""
    if max_width <= 0:
        return ""
    if font.size(text)[0] <= max_width:
        return text
    suffix = "…"
    candidate = text
    while candidate and font.size(candidate + suffix)[0] > max_width:
        candidate = candidate[:-1]
    return candidate.rstrip() + suffix


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> tuple[str, ...]:
    """Wrap a sentence into lines that fit inside a pixel width."""
    words = text.split()
    if not words:
        return ("",)
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return tuple(lines)


def draw_wrapped_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: Color,
    rect: pygame.Rect,
    *,
    line_gap: int = 3,
    max_lines: int | None = None,
) -> int:
    """Draw wrapped text and return the y coordinate below the final line."""
    lines = list(wrap_text(font, text, rect.width))
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = ellipsize(font, lines[-1], rect.width)
    y = rect.y
    for line in lines:
        draw_text(surface, font, line, color, (rect.x, y))
        y += font.get_linesize() + line_gap
    return y


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    color: Color = PALETTE.panel,
    border_color: Color = PALETTE.edge,
    radius: int = 10,
) -> None:
    """Draw a filled panel with a subtle border."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, width=1, border_radius=radius)


def draw_button(
    surface: pygame.Surface,
    fonts: Fonts,
    rect: pygame.Rect,
    label: str,
    *,
    primary: bool = False,
    selected: bool = False,
    enabled: bool = True,
    compact: bool = False,
) -> None:
    """Draw a reusable text button."""
    if not enabled:
        background = PALETTE.panel_alt
        foreground = PALETTE.muted
        border = PALETTE.edge
    elif primary:
        background = PALETTE.cyan
        foreground = PALETTE.deep
        border = PALETTE.cyan
    elif selected:
        background = PALETTE.cyan_soft
        foreground = PALETTE.cyan
        border = PALETTE.cyan_dark
    else:
        background = PALETTE.panel_alt
        foreground = PALETTE.text
        border = PALETTE.edge
    pygame.draw.rect(surface, background, rect, border_radius=7)
    pygame.draw.rect(surface, border, rect, width=1, border_radius=7)
    font = fonts.small if compact else fonts.body
    draw_text(surface, font, label, foreground, rect.center, anchor="center")


def draw_progress(
    surface: pygame.Surface,
    rect: pygame.Rect,
    value: float,
) -> None:
    """Draw a zero-to-one progress indicator."""
    normalized = max(0.0, min(1.0, value))
    pygame.draw.rect(surface, PALETTE.panel_alt, rect, border_radius=rect.height // 2)
    fill_rect = pygame.Rect(rect.x, rect.y, round(rect.width * normalized), rect.height)
    if fill_rect.width > 0:
        pygame.draw.rect(
            surface,
            PALETTE.cyan,
            fill_rect,
            border_radius=rect.height // 2,
        )
