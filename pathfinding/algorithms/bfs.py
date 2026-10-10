"""Breadth-First Search: shortest path in number of moves (ignores weights)."""

from __future__ import annotations

from collections import deque
from typing import Iterator, Optional

from ..grid import Grid, Node
from .base import DONE, FRONTIER, VISIT, Step, reconstruct_path


def bfs(grid: Grid, start: Node, goal: Node, diagonal: bool = False) -> Iterator[Step]:
    came_from: dict[Node, Optional[Node]] = {start: None}
    queue: deque[Node] = deque([start])
    while queue:
        current = queue.popleft()
        yield Step(VISIT, current)
        if current == goal:
            yield Step(DONE, path=reconstruct_path(came_from, goal))
            return
        for nb, _ in grid.neighbors(current, diagonal):
            if nb not in came_from:
                came_from[nb] = current
                queue.append(nb)
                yield Step(FRONTIER, nb)
    yield Step(DONE, path=None)
