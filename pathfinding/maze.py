"""Maze and obstacle generators operating on a :class:`~pathfinding.grid.Grid`."""

from __future__ import annotations

import random

from .grid import Grid, Node


def _odd_cell(value: int, limit: int) -> int:
    """Clamp ``value`` to the nearest odd index inside ``[1, limit - 2]``."""
    value = max(1, min(value, limit - 2))
    return value if value % 2 == 1 else value - 1


def recursive_backtracker(grid: Grid, seed: int | None = None) -> None:
    """Fill ``grid`` with a perfect maze using an iterative recursive backtracker.

    Corridors live on odd coordinates; start and goal are snapped onto the
    nearest corridor cell so they are always connected.
    """
    rng = random.Random(seed)
    grid.clear_walls()
    if grid.cols < 3 or grid.rows < 3:
        return
    grid.walls = {(c, r) for c in range(grid.cols) for r in range(grid.rows)}

    first = (1, 1)
    grid.walls.discard(first)
    stack: list[Node] = [first]
    while stack:
        c, r = stack[-1]
        options = []
        for dc, dr in ((0, -2), (2, 0), (0, 2), (-2, 0)):
            nc, nr = c + dc, r + dr
            if 0 < nc < grid.cols - 1 and 0 < nr < grid.rows - 1 and (nc, nr) in grid.walls:
                options.append((nc, nr, c + dc // 2, r + dr // 2))
        if not options:
            stack.pop()
            continue
        nc, nr, wc, wr = rng.choice(options)
        grid.walls.discard((wc, wr))
        grid.walls.discard((nc, nr))
        stack.append((nc, nr))

    start = (_odd_cell(grid.start[0], grid.cols), _odd_cell(grid.start[1], grid.rows))
    goal = (_odd_cell(grid.goal[0], grid.cols), _odd_cell(grid.goal[1], grid.rows))
    if goal == start:
        goal = (_odd_cell(grid.cols - 2, grid.cols), _odd_cell(grid.rows - 2, grid.rows))
    grid.start, grid.goal = start, goal
    grid.walls.discard(start)
    grid.walls.discard(goal)


def random_walls(grid: Grid, density: float = 0.3, seed: int | None = None) -> None:
    """Scatter walls randomly over ``density`` fraction of the cells."""
    rng = random.Random(seed)
    grid.clear_walls()
    for c in range(grid.cols):
        for r in range(grid.rows):
            if (c, r) not in (grid.start, grid.goal) and rng.random() < density:
                grid.walls.add((c, r))


def random_weights(grid: Grid, density: float = 0.25, weight: int = 5, seed: int | None = None) -> None:
    """Scatter weighted cells over free cells (keeps existing walls)."""
    rng = random.Random(seed)
    for c in range(grid.cols):
        for r in range(grid.rows):
            node = (c, r)
            if node not in grid.walls and node not in (grid.start, grid.goal) and rng.random() < density:
                grid.weights[node] = weight
