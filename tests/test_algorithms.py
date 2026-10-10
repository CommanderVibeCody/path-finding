import random

import pytest

from pathfinding.algorithms import (
    ALGORITHMS, DONE, VISIT, astar, bfs, bidirectional_bfs, dijkstra, run,
)
from pathfinding.grid import Grid
from pathfinding.maze import random_walls, recursive_backtracker

ALL = [info.func for info in ALGORITHMS]
UNWEIGHTED_OPTIMAL = [bfs, bidirectional_bfs, dijkstra, astar]
WEIGHTED_OPTIMAL = [dijkstra, astar]

OPEN = [
    "S.........",
    "..........",
    "..........",
    ".........G",
]

WALLED = [
    "S...#.....",
    ".##.#.###.",
    ".#..#...#.",
    ".#.###.#..",
    ".......#.G",
]

BLOCKED = [
    "S..#......",
    "...#......",
    "####......",
    ".........G",
]


def assert_valid_path(grid: Grid, path, diagonal=False):
    assert path[0] == grid.start
    assert path[-1] == grid.goal
    for a, b in zip(path, path[1:]):
        assert b in {n for n, _ in grid.neighbors(a, diagonal)}, f"illegal move {a}->{b}"
    assert not set(path) & grid.walls


def bfs_distance(grid: Grid, diagonal=False):
    return run(bfs, grid, diagonal=diagonal).length


@pytest.mark.parametrize("algo", ALL, ids=lambda f: f.__name__)
@pytest.mark.parametrize("layout", [OPEN, WALLED], ids=["open", "walled"])
def test_finds_valid_path(algo, layout):
    grid = Grid.from_strings(layout)
    result = run(algo, grid)
    assert result.found
    assert_valid_path(grid, result.path)


@pytest.mark.parametrize("algo", ALL, ids=lambda f: f.__name__)
def test_no_path_when_blocked(algo):
    grid = Grid.from_strings(BLOCKED)
    result = run(algo, grid)
    assert result.path is None
    assert result.visited > 0


@pytest.mark.parametrize("algo", ALL, ids=lambda f: f.__name__)
def test_start_equals_goal(algo):
    grid = Grid(5, 5, start=(2, 2), goal=(2, 2))
    assert run(algo, grid).path == [(2, 2)]


@pytest.mark.parametrize("algo", ALL, ids=lambda f: f.__name__)
def test_generator_ends_with_single_done(algo):
    grid = Grid.from_strings(WALLED)
    steps = list(algo(grid, grid.start, grid.goal))
    assert steps[-1].kind == DONE
    assert sum(s.kind == DONE for s in steps) == 1
    assert any(s.kind == VISIT for s in steps)


@pytest.mark.parametrize("algo", UNWEIGHTED_OPTIMAL, ids=lambda f: f.__name__)
def test_shortest_on_known_grids(algo):
    assert run(algo, Grid.from_strings(OPEN)).length == 12
    assert run(algo, Grid.from_strings(WALLED)).length == bfs_distance(Grid.from_strings(WALLED))


@pytest.mark.parametrize("algo", UNWEIGHTED_OPTIMAL, ids=lambda f: f.__name__)
@pytest.mark.parametrize("diagonal", [False, True], ids=["4way", "8way"])
@pytest.mark.parametrize("seed", range(25))
def test_shortest_matches_bfs_on_random_grids(algo, diagonal, seed):
    grid = Grid(21, 15, start=(0, 0), goal=(20, 14))
    random_walls(grid, density=0.3, seed=seed)
    expected = run(bfs, grid, diagonal=diagonal)
    result = run(algo, grid, diagonal=diagonal)
    assert result.found == expected.found
    if expected.found:
        assert_valid_path(grid, result.path, diagonal)
        if diagonal and algo in (dijkstra, astar):
            # With diagonals, cost-optimal paths can have more moves; compare costs instead.
            assert result.cost <= grid.path_cost(expected.path) + 1e-9
        else:
            assert result.length == expected.length


@pytest.mark.parametrize("diagonal", [False, True], ids=["4way", "8way"])
@pytest.mark.parametrize("seed", range(25))
def test_astar_matches_dijkstra_cost_with_weights(diagonal, seed):
    rng = random.Random(seed)
    grid = Grid(21, 15, start=(0, 0), goal=(20, 14))
    random_walls(grid, density=0.2, seed=seed)
    for c in range(grid.cols):
        for r in range(grid.rows):
            if (c, r) not in grid.walls and (c, r) not in (grid.start, grid.goal) and rng.random() < 0.3:
                grid.weights[(c, r)] = 5
    d = run(dijkstra, grid, diagonal=diagonal)
    a = run(astar, grid, diagonal=diagonal)
    assert d.found == a.found
    if d.found:
        assert a.cost == pytest.approx(d.cost)
        assert a.visited <= d.visited


@pytest.mark.parametrize("algo", WEIGHTED_OPTIMAL, ids=lambda f: f.__name__)
def test_weighted_algorithms_avoid_heavy_cells(algo):
    # Going straight costs 9*4 + 1; going around the mud costs 6 moves of cost 1.
    grid = Grid.from_strings([
        "S99G",
        "....",
    ])
    result = run(algo, grid)
    assert result.cost == 5  # down, 3x right, up
    assert (1, 0) not in result.path and (2, 0) not in result.path


def test_bfs_ignores_weights():
    grid = Grid.from_strings(["S99G", "...."])
    assert run(bfs, grid).length == 3


def test_diagonal_does_not_cut_corners():
    grid = Grid.from_strings([
        "S#",
        "#G",
    ])
    assert run(bfs, grid, diagonal=True).path is None


def test_diagonal_shortens_path():
    grid = Grid.from_strings(OPEN)
    assert run(bfs, grid, diagonal=True).length == 9


@pytest.mark.parametrize("seed", range(5))
def test_maze_is_solvable_by_all(seed):
    grid = Grid(35, 29)
    recursive_backtracker(grid, seed=seed)
    lengths = {}
    for info in ALGORITHMS:
        result = run(info.func, grid)
        assert result.found, info.name
        assert_valid_path(grid, result.path)
        lengths[info.name] = result.length
    # A perfect maze has exactly one simple path, so every algorithm agrees.
    assert len(set(lengths.values())) == 1
