"""Dijkstra's algorithm: cheapest path on weighted grids."""

from __future__ import annotations

import heapq
import itertools
from typing import Iterator, Optional

from ..grid import Grid, Node
from .base import DONE, FRONTIER, VISIT, Step, reconstruct_path


def dijkstra(grid: Grid, start: Node, goal: Node, diagonal: bool = False) -> Iterator[Step]:
    counter = itertools.count()
    dist: dict[Node, float] = {start: 0.0}
    came_from: dict[Node, Optional[Node]] = {start: None}
    closed: set[Node] = set()
    heap: list[tuple[float, int, Node]] = [(0.0, next(counter), start)]
    while heap:
        d, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        yield Step(VISIT, current)
        if current == goal:
            yield Step(DONE, path=reconstruct_path(came_from, goal))
            return
        for nb, cost in grid.neighbors(current, diagonal):
            nd = d + cost
            if nb not in closed and nd < dist.get(nb, float("inf")):
                dist[nb] = nd
                came_from[nb] = current
                heapq.heappush(heap, (nd, next(counter), nb))
                yield Step(FRONTIER, nb)
    yield Step(DONE, path=None)
