"""A* search: Dijkstra guided by an admissible heuristic (Manhattan / octile)."""

from __future__ import annotations

import heapq
import itertools
from typing import Iterator, Optional

from ..grid import Grid, Node
from .base import DONE, FRONTIER, VISIT, Step, heuristic_for, reconstruct_path


def astar(grid: Grid, start: Node, goal: Node, diagonal: bool = False) -> Iterator[Step]:
    h = heuristic_for(diagonal)
    counter = itertools.count()
    g: dict[Node, float] = {start: 0.0}
    came_from: dict[Node, Optional[Node]] = {start: None}
    closed: set[Node] = set()
    # Ties on f are broken by the lower heuristic (closer to the goal) first.
    heap: list[tuple[float, float, int, Node]] = [(h(start, goal), h(start, goal), next(counter), start)]
    while heap:
        _, _, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        yield Step(VISIT, current)
        if current == goal:
            yield Step(DONE, path=reconstruct_path(came_from, goal))
            return
        for nb, cost in grid.neighbors(current, diagonal):
            ng = g[current] + cost
            if nb not in closed and ng < g.get(nb, float("inf")):
                g[nb] = ng
                came_from[nb] = current
                hn = h(nb, goal)
                heapq.heappush(heap, (ng + hn, hn, next(counter), nb))
                yield Step(FRONTIER, nb)
    yield Step(DONE, path=None)
