"""Headless smoke tests for the Pygame front-end (uses SDL's dummy video driver)."""

import os

import pygame
import pytest

from pathfinding.algorithms import ALGORITHMS
from pathfinding.app import FINISHED, SEARCHING, App


@pytest.fixture
def app():
    assert os.environ.get("SDL_VIDEODRIVER") == "dummy"
    application = App()
    yield application
    pygame.quit()


def press(app, key):
    app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode=""))


def mouse(app, kind, pos, button=1):
    if kind == "motion":
        app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(1, 0, 0)))
    else:
        etype = pygame.MOUSEBUTTONDOWN if kind == "down" else pygame.MOUSEBUTTONUP
        app.handle_event(pygame.event.Event(etype, pos=pos, button=button))


def cell_center(app, node):
    return (node[0] * app.cell + app.cell // 2, node[1] * app.cell + app.cell // 2)


def run_until_finished(app, max_frames=20000):
    for _ in range(max_frames):
        app.step_frame()
        if app.state == FINISHED:
            return
    raise AssertionError("animation did not finish")


def test_main_loop_frames(app):
    for _ in range(10):
        app.step_frame()
    assert app.running


@pytest.mark.parametrize("index", range(len(ALGORITHMS)))
def test_each_algorithm_animates(app, index):
    press(app, pygame.K_m)  # maze
    press(app, pygame.K_1 + index)
    for _ in range(5):
        press(app, pygame.K_PLUS)
    press(app, pygame.K_SPACE)
    assert app.state == SEARCHING
    run_until_finished(app)
    assert app.path and app.path_shown == len(app.path)
    assert app.path[0] == app.grid.start and app.path[-1] == app.grid.goal


def test_drawing_walls_and_moving_endpoints(app):
    # Drag a wall line between two cells (interpolated).
    mouse(app, "down", cell_center(app, (5, 2)))
    mouse(app, "motion", cell_center(app, (5, 10)))
    mouse(app, "up", cell_center(app, (5, 10)))
    assert all((5, r) in app.grid.walls for r in range(2, 11))

    # Right-drag erases.
    mouse(app, "down", cell_center(app, (5, 4)), button=3)
    mouse(app, "up", cell_center(app, (5, 4)), button=3)
    assert (5, 4) not in app.grid.walls

    # Drag the start node somewhere else.
    old_start = app.grid.start
    mouse(app, "down", cell_center(app, old_start))
    mouse(app, "motion", cell_center(app, (2, 2)))
    mouse(app, "up", cell_center(app, (2, 2)))
    assert app.grid.start == (2, 2)

    # Weight brush.
    press(app, pygame.K_w)
    mouse(app, "down", cell_center(app, (8, 8)))
    mouse(app, "up", cell_center(app, (8, 8)))
    assert app.grid.weights.get((8, 8)) == 5


def test_live_update_after_finished(app):
    app.solve_instantly()
    assert app.state == FINISHED and app.path
    blocker = app.path[len(app.path) // 2]
    mouse(app, "down", cell_center(app, blocker))
    mouse(app, "up", cell_center(app, blocker))
    assert blocker in app.grid.walls
    assert app.state == FINISHED and blocker not in app.path


def test_buttons_and_toggles(app):
    for button in app.buttons:
        button.action()
        app.step_frame()
    press(app, pygame.K_d)
    press(app, pygame.K_t)
    press(app, pygame.K_r)
    press(app, pygame.K_x)
    assert not app.grid.walls and not app.grid.weights
    press(app, pygame.K_c)
    for _ in range(3):
        app.step_frame()


def test_no_path_reported(app):
    gx, gy = app.grid.goal
    for dc, dr in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        app.grid.set_wall((gx + dc, gy + dr))
    app.solve_instantly()
    assert app.result is not None and not app.result.found
    app.draw()


def test_escape_quits(app):
    press(app, pygame.K_ESCAPE)
    assert not app.running
