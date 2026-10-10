"""Greedy Best-First Search: follows the heuristic only. Fast, not optimal."""

from __future__ import annotations

import heapq
import itertools
from typing import Iterator, Optional

from ..grid import Grid, Node
from .base import DONE, FRONTIER, VISIT, Step, heuristic_for, reconstruct_path


def greedy_best_first(grid: Grid, start: Node, goal: Node, diagonal: bool = False) -> Iterator[Step]:
    h = heuristic_for(diagonal)
    counter = itertools.count()
    came_from: dict[Node, Optional[Node]] = {start: None}
    closed: set[Node] = set()
    heap: list[tuple[float, int, Node]] = [(h(start, goal), next(counter), start)]
    while heap:
        _, _, current = heapq.heappop(heap)
        if current in closed:
            continue
        closed.add(current)
        yield Step(VISIT, current)
        if current == goal:
            yield Step(DONE, path=reconstruct_path(came_from, goal))
            return
        for nb, _ in grid.neighbors(current, diagonal):
            if nb not in came_from:
                came_from[nb] = current
                heapq.heappush(heap, (h(nb, goal), next(counter), nb))
                yield Step(FRONTIER, nb)
    yield Step(DONE, path=None)
