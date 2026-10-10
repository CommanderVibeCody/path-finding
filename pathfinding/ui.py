"""Rendering helpers: colours, buttons and the side panel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pygame

# ----------------------------------------------------------------------------- colours
BG = (24, 26, 33)
PANEL_BG = (32, 35, 45)
GRID_LINE = (205, 210, 220)
EMPTY = (245, 246, 250)
WALL = (40, 44, 58)
WEIGHT = (176, 130, 92)
VISITED = (120, 190, 235)
FRONTIER = (150, 230, 170)
PATH = (255, 214, 64)
START = (46, 184, 92)
GOAL = (230, 70, 80)
TEXT = (230, 232, 240)
TEXT_DIM = (150, 155, 170)
ACCENT = (98, 132, 255)
BUTTON = (52, 57, 72)
BUTTON_HOVER = (68, 74, 94)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: Callable[[], None]
    is_active: Callable[[], bool] = field(default=lambda: False)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, mouse: tuple[int, int]) -> None:
        if self.is_active():
            colour = ACCENT
        elif self.rect.collidepoint(mouse):
            colour = BUTTON_HOVER
        else:
            colour = BUTTON
        pygame.draw.rect(surface, colour, self.rect, border_radius=6)
        text = font.render(self.label, True, TEXT)
        surface.blit(text, text.get_rect(midleft=(self.rect.x + 10, self.rect.centery)))

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False


class Fonts:
    def __init__(self) -> None:
        self.title = pygame.font.Font(None, 30)
        self.normal = pygame.font.Font(None, 22)
        self.small = pygame.font.Font(None, 19)
        self.cell = pygame.font.Font(None, 18)


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Linear mix of two colours (``t`` = share of ``b``)."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))  # type: ignore[return-value]


def draw_text(surface: pygame.Surface, font: pygame.font.Font, text: str, pos: tuple[int, int],
              colour: tuple[int, int, int] = TEXT) -> int:
    """Blit ``text`` at ``pos`` and return the y coordinate below it."""
    img = font.render(text, True, colour)
    surface.blit(img, pos)
    return pos[1] + img.get_height() + 4


def draw_legend(surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> int:
    items = [(START, "Start"), (GOAL, "Goal"), (WALL, "Wall"), (WEIGHT, "Weight"),
             (FRONTIER, "Frontier"), (VISITED, "Visited"), (PATH, "Path")]
    for i, (colour, label) in enumerate(items):
        cx = x + (i % 2) * 115
        cy = y + (i // 2) * 20
        pygame.draw.rect(surface, colour, (cx, cy + 2, 13, 13), border_radius=3)
        surface.blit(font.render(label, True, TEXT_DIM), (cx + 19, cy + 1))
    return y + ((len(items) + 1) // 2) * 20 + 4
