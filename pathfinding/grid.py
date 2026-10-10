"""Pure grid model: walls, weighted cells, start/goal and neighbour lookup.

This module has no Pygame dependency so it can be used (and tested) on its own.
"""

from __future__ import annotations

import math
from typing import Iterable

Node = tuple[int, int]  # (col, row)

# Weight assigned to "heavy" cells (e.g. mud). Normal cells cost 1.
DEFAULT_WEIGHT = 5

ORTHOGONAL: tuple[Node, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))  # up, right, down, left
DIAGONAL: tuple[Node, ...] = ((1, -1), (1, 1), (-1, 1), (-1, -1))
SQRT2 = math.sqrt(2)


class Grid:
    """A rectangular grid of cells addressed as ``(col, row)``."""

    def __init__(self, cols: int, rows: int, start: Node | None = None, goal: Node | None = None):
        if cols < 2 or rows < 1:
            raise ValueError("grid must be at least 2x1")
        self.cols = cols
        self.rows = rows
        self.walls: set[Node] = set()
        self.weights: dict[Node, int] = {}
        self.start: Node = start if start is not None else (1 if cols > 2 else 0, rows // 2)
        self.goal: Node = goal if goal is not None else (cols - 2 if cols > 2 else cols - 1, rows // 2)

    # ------------------------------------------------------------------ queries
    def in_bounds(self, node: Node) -> bool:
        c, r = node
        return 0 <= c < self.cols and 0 <= r < self.rows

    def is_wall(self, node: Node) -> bool:
        return node in self.walls

    def passable(self, node: Node) -> bool:
        return self.in_bounds(node) and node not in self.walls

    def weight(self, node: Node) -> int:
        """Cost of entering ``node`` (1 for normal cells)."""
        return self.weights.get(node, 1)

    def neighbors(self, node: Node, diagonal: bool = False) -> list[tuple[Node, float]]:
        """Return ``(neighbour, move_cost)`` pairs reachable from ``node``.

        Diagonal moves are only allowed when both adjacent orthogonal cells are
        free, so paths never cut through wall corners.
        """
        c, r = node
        result: list[tuple[Node, float]] = []
        for dc, dr in ORTHOGONAL:
            nb = (c + dc, r + dr)
            if self.passable(nb):
                result.append((nb, float(self.weight(nb))))
        if diagonal:
            for dc, dr in DIAGONAL:
                nb = (c + dc, r + dr)
                if (
                    self.passable(nb)
                    and self.passable((c + dc, r))
                    and self.passable((c, r + dr))
                ):
                    result.append((nb, SQRT2 * self.weight(nb)))
        return result

    def path_cost(self, path: Iterable[Node]) -> float:
        """Total cost of following ``path`` (cost of every entered cell)."""
        total = 0.0
        prev: Node | None = None
        for node in path:
            if prev is not None:
                step = SQRT2 if (node[0] != prev[0] and node[1] != prev[1]) else 1.0
                total += step * self.weight(node)
            prev = node
        return total

    # ------------------------------------------------------------------ editing
    def set_wall(self, node: Node) -> bool:
        if not self.in_bounds(node) or node in (self.start, self.goal):
            return False
        self.weights.pop(node, None)
        self.walls.add(node)
        return True

    def set_weight(self, node: Node, weight: int = DEFAULT_WEIGHT) -> bool:
        if not self.in_bounds(node) or node in (self.start, self.goal):
            return False
        self.walls.discard(node)
        self.weights[node] = weight
        return True

    def clear_cell(self, node: Node) -> bool:
        changed = node in self.walls or node in self.weights
        self.walls.discard(node)
        self.weights.pop(node, None)
        return changed

    def clear_walls(self) -> None:
        self.walls.clear()
        self.weights.clear()

    def move_start(self, node: Node) -> bool:
        if self.passable(node) and node != self.goal:
            self.weights.pop(node, None)
            self.start = node
            return True
        return False

    def move_goal(self, node: Node) -> bool:
        if self.passable(node) and node != self.start:
            self.weights.pop(node, None)
            self.goal = node
            return True
        return False

    # ------------------------------------------------------------------ helpers
    @classmethod
    def from_strings(cls, lines: list[str]) -> "Grid":
        """Build a grid from ASCII art (handy for tests).

        ``#`` wall, ``S`` start, ``G`` goal, a digit ``2-9`` a weighted cell,
        anything else an empty cell.
        """
        rows = len(lines)
        cols = max(len(line) for line in lines)
        grid = cls(cols, rows, start=(0, 0), goal=(cols - 1, rows - 1))
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == "#":
                    grid.walls.add((c, r))
                elif ch == "S":
                    grid.start = (c, r)
                elif ch == "G":
                    grid.goal = (c, r)
                elif ch.isdigit() and int(ch) > 1:
                    grid.weights[(c, r)] = int(ch)
        return grid
