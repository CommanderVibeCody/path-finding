"""Bidirectional BFS: two BFS waves from start and goal that meet in the middle.

Finds a shortest path in number of moves (ignores weights) while usually
exploring far fewer cells than a single BFS.
"""

from __future__ import annotations

from typing import Generator, Iterator, Optional

from ..grid import Grid, Node
from .base import DONE, FRONTIER, VISIT, Step

Parents = dict[Node, Optional[Node]]


def _expand_layer(
    grid: Grid, layer: list[Node], parents: Parents, depth: dict[Node, int],
    other_depth: dict[Node, int], diagonal: bool,
) -> Generator[Step, None, tuple[list[Node], Optional[Node]]]:
    """Expand one whole BFS layer; return the next layer and the best meeting node."""
    next_layer: list[Node] = []
    best: Optional[Node] = None
    for current in layer:
        yield Step(VISIT, current)
        for nb, _ in grid.neighbors(current, diagonal):
            if nb in depth:
                continue
            parents[nb] = current
            depth[nb] = depth[current] + 1
            next_layer.append(nb)
            yield Step(FRONTIER, nb)
            if nb in other_depth and (best is None or other_depth[nb] < other_depth[best]):
                best = nb
    return next_layer, best


def _chain(parents: Parents, node: Node) -> list[Node]:
    out = [node]
    while (prev := parents[out[-1]]) is not None:
        out.append(prev)
    return out


def bidirectional_bfs(grid: Grid, start: Node, goal: Node, diagonal: bool = False) -> Iterator[Step]:
    if start == goal:
        yield Step(VISIT, start)
        yield Step(DONE, path=[start])
        return
    fwd_parents: Parents = {start: None}
    bwd_parents: Parents = {goal: None}
    fwd_depth = {start: 0}
    bwd_depth = {goal: 0}
    fwd_layer, bwd_layer = [start], [goal]

    while fwd_layer and bwd_layer:
        # Always grow the smaller wave to keep the search balanced.
        if len(fwd_layer) <= len(bwd_layer):
            fwd_layer, meet = yield from _expand_layer(
                grid, fwd_layer, fwd_parents, fwd_depth, bwd_depth, diagonal)
        else:
            bwd_layer, meet = yield from _expand_layer(
                grid, bwd_layer, bwd_parents, bwd_depth, fwd_depth, diagonal)
        if meet is not None:
            path = list(reversed(_chain(fwd_parents, meet))) + _chain(bwd_parents, meet)[1:]
            yield Step(DONE, path=path)
            return
    yield Step(DONE, path=None)
