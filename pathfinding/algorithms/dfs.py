"""Depth-First Search: finds *a* path, usually far from the shortest one."""

from __future__ import annotations

from typing import Iterator, Optional

from ..grid import Grid, Node
from .base import DONE, FRONTIER, VISIT, Step, reconstruct_path


def dfs(grid: Grid, start: Node, goal: Node, diagonal: bool = False) -> Iterator[Step]:
    came_from: dict[Node, Optional[Node]] = {start: None}
    visited: set[Node] = set()
    stack: list[Node] = [start]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        yield Step(VISIT, current)
        if current == goal:
            yield Step(DONE, path=reconstruct_path(came_from, goal))
            return
        # Push in reverse so the first neighbour (up) is explored first.
        for nb, _ in reversed(grid.neighbors(current, diagonal)):
            if nb not in visited:
                came_from[nb] = current
                stack.append(nb)
                yield Step(FRONTIER, nb)
    yield Step(DONE, path=None)
