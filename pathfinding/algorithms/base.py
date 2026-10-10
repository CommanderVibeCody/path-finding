"""Shared types and helpers for the search algorithms.

Every algorithm is a *generator function* with the signature::

    algorithm(grid, start, goal, diagonal=False) -> Iterator[Step]

It yields :class:`Step` events while it explores the grid and always finishes
with exactly one ``DONE`` step whose ``path`` is the found path (start..goal)
or ``None`` if the goal is unreachable. Algorithms never touch rendering code,
which keeps them easy to test and to animate.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

from ..grid import SQRT2, Grid, Node

VISIT = "visit"        # node was expanded / closed
FRONTIER = "frontier"  # node was added to the open set
DONE = "done"          # search finished; see Step.path


@dataclass(frozen=True)
class Step:
    kind: str
    node: Optional[Node] = None
    path: Optional[list[Node]] = None


SearchFn = Callable[..., Iterator[Step]]


@dataclass
class SearchResult:
    path: Optional[list[Node]]
    visited: int
    cost: float
    elapsed_ms: float

    @property
    def found(self) -> bool:
        return self.path is not None

    @property
    def length(self) -> int:
        """Number of moves in the path (0 if no path)."""
        return len(self.path) - 1 if self.path else 0


def run(algorithm: SearchFn, grid: Grid, start: Node | None = None, goal: Node | None = None,
        diagonal: bool = False) -> SearchResult:
    """Run ``algorithm`` to completion without visualisation and collect stats."""
    start = grid.start if start is None else start
    goal = grid.goal if goal is None else goal
    visited = 0
    path: Optional[list[Node]] = None
    t0 = time.perf_counter()
    for step in algorithm(grid, start, goal, diagonal):
        if step.kind == VISIT:
            visited += 1
        elif step.kind == DONE:
            path = step.path
    elapsed = (time.perf_counter() - t0) * 1000
    cost = grid.path_cost(path) if path else 0.0
    return SearchResult(path, visited, cost, elapsed)


def reconstruct_path(came_from: dict[Node, Optional[Node]], goal: Node) -> list[Node]:
    path = [goal]
    while (prev := came_from[path[-1]]) is not None:
        path.append(prev)
    path.reverse()
    return path


def manhattan(a: Node, b: Node) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def octile(a: Node, b: Node) -> float:
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return (dx + dy) + (SQRT2 - 2) * min(dx, dy)


def heuristic_for(diagonal: bool) -> Callable[[Node, Node], float]:
    """Admissible heuristic: Manhattan for 4-way moves, octile for 8-way moves."""
    return octile if diagonal else manhattan
