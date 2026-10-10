"""Path-finding algorithms as pure, step-yielding generators."""

from __future__ import annotations

from dataclasses import dataclass

from .astar import astar
from .base import DONE, FRONTIER, VISIT, SearchFn, SearchResult, Step, run
from .bfs import bfs
from .bidirectional import bidirectional_bfs
from .dfs import dfs
from .dijkstra import dijkstra
from .greedy import greedy_best_first


@dataclass(frozen=True)
class AlgorithmInfo:
    name: str
    func: SearchFn
    weighted: bool   # takes cell weights into account
    shortest: bool   # guarantees an optimal path (in moves, or in cost if weighted)


ALGORITHMS: list[AlgorithmInfo] = [
    AlgorithmInfo("A* Search", astar, weighted=True, shortest=True),
    AlgorithmInfo("Dijkstra", dijkstra, weighted=True, shortest=True),
    AlgorithmInfo("Breadth-First Search", bfs, weighted=False, shortest=True),
    AlgorithmInfo("Depth-First Search", dfs, weighted=False, shortest=False),
    AlgorithmInfo("Greedy Best-First", greedy_best_first, weighted=True, shortest=False),
    AlgorithmInfo("Bidirectional BFS", bidirectional_bfs, weighted=False, shortest=True),
]

__all__ = [
    "ALGORITHMS", "AlgorithmInfo", "DONE", "FRONTIER", "VISIT", "SearchFn", "SearchResult", "Step",
    "astar", "bfs", "bidirectional_bfs", "dfs", "dijkstra", "greedy_best_first", "run",
]
