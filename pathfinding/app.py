"""The interactive Pygame application: input handling, animation and drawing."""

from __future__ import annotations

from typing import Iterator, Optional

import pygame

from . import ui
from .algorithms import ALGORITHMS, DONE, FRONTIER, VISIT, SearchResult, Step, run
from .grid import DEFAULT_WEIGHT, Grid, Node
from .maze import random_walls, random_weights, recursive_backtracker

CELL = 24
COLS, ROWS = 35, 29
PANEL_WIDTH = 270
FPS = 60
SPEEDS = [1, 2, 5, 10, 25, 100]  # search steps per frame
SPEED_NAMES = ["Very slow", "Slow", "Normal", "Fast", "Very fast", "Instant-ish"]

IDLE, SEARCHING, TRACING, FINISHED = "idle", "searching", "tracing", "finished"


def line_cells(a: Node, b: Node) -> list[Node]:
    """Cells on a straight line from ``a`` to ``b`` (Bresenham), so fast drags leave no gaps."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    cells = []
    while True:
        cells.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return cells
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


class App:
    def __init__(self, cols: int = COLS, rows: int = ROWS, cell: int = CELL) -> None:
        # Only the modules we need (avoids audio initialisation on machines without sound).
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Path-Finding Visualizer")
        self.cell = cell
        self.grid = Grid(cols, rows)
        self.grid_px = (cols * cell, rows * cell)
        self.screen = pygame.display.set_mode((self.grid_px[0] + PANEL_WIDTH, self.grid_px[1]))
        self.clock = pygame.time.Clock()
        self.fonts = ui.Fonts()
        self.running = True

        self.algo_index = 0
        self.diagonal = False
        self.brush = "wall"  # or "weight"
        self.speed_index = 2

        self.state = IDLE
        self.search: Optional[Iterator[Step]] = None
        self.visited: set[Node] = set()
        self.frontier: set[Node] = set()
        self.path: list[Node] = []
        self.path_shown = 0
        self.result: Optional[SearchResult] = None

        self.drag_mode: Optional[str] = None  # "paint", "erase", "start", "goal"
        self.last_cell: Optional[Node] = None
        self.buttons: list[ui.Button] = []
        self._build_panel()

    # ------------------------------------------------------------------ panel layout
    def _build_panel(self) -> None:
        x0 = self.grid_px[0] + 15
        width = PANEL_WIDTH - 30
        y = 50
        self.algo_label_y = y
        y += 24
        for i, info in enumerate(ALGORITHMS):
            rect = pygame.Rect(x0, y, width, 24)
            self.buttons.append(ui.Button(rect, f"{i + 1}  {info.name}",
                                          lambda i=i: self.select_algorithm(i),
                                          lambda i=i: self.algo_index == i))
            y += 28
        y += 6
        self.actions_label_y = y
        y += 24
        half = (width - 8) // 2
        actions = [
            ("Run [Space]", self.start_search, lambda: self.state in (SEARCHING, TRACING)),
            ("Clear path [C]", self.clear_search, lambda: False),
            ("Clear all [X]", self.clear_walls, lambda: False),
            ("Maze [M]", self.generate_maze, lambda: False),
            ("Rand. walls [R]", self.generate_random_walls, lambda: False),
            ("Weights [T]", self.generate_random_weights, lambda: False),
            ("Brush [W]", self.toggle_brush, lambda: self.brush == "weight"),
            ("Diagonal [D]", self.toggle_diagonal, lambda: self.diagonal),
            ("Slower [-]", lambda: self.change_speed(-1), lambda: False),
            ("Faster [+]", lambda: self.change_speed(1), lambda: False),
        ]
        for i, (label, action, active) in enumerate(actions):
            rect = pygame.Rect(x0 + (i % 2) * (half + 8), y + (i // 2) * 28, half, 24)
            self.buttons.append(ui.Button(rect, label, action, active))
        self.stats_y = y + ((len(actions) + 1) // 2) * 28 + 6

    # ------------------------------------------------------------------ actions
    def select_algorithm(self, index: int) -> None:
        self.algo_index = index
        self._after_change()

    def toggle_diagonal(self) -> None:
        self.diagonal = not self.diagonal
        self._after_change()

    def toggle_brush(self) -> None:
        self.brush = "weight" if self.brush == "wall" else "wall"

    def change_speed(self, delta: int) -> None:
        self.speed_index = max(0, min(len(SPEEDS) - 1, self.speed_index + delta))

    def clear_search(self) -> None:
        self.state = IDLE
        self.search = None
        self.visited.clear()
        self.frontier.clear()
        self.path = []
        self.path_shown = 0
        self.result = None

    def clear_walls(self) -> None:
        self.grid.clear_walls()
        self.clear_search()

    def generate_maze(self) -> None:
        self.clear_search()
        recursive_backtracker(self.grid)

    def generate_random_walls(self) -> None:
        self.clear_search()
        random_walls(self.grid)

    def generate_random_weights(self) -> None:
        random_weights(self.grid)
        self._after_change()

    def start_search(self) -> None:
        """Start an animated run of the selected algorithm."""
        self.clear_search()
        info = ALGORITHMS[self.algo_index]
        # Stats (incl. timing) come from an un-animated run of the pure algorithm.
        self.result = run(info.func, self.grid, diagonal=self.diagonal)
        self.search = info.func(self.grid, self.grid.start, self.grid.goal, self.diagonal)
        self.state = SEARCHING

    def solve_instantly(self) -> None:
        """Run the selected algorithm to completion without animation."""
        self.start_search()
        assert self.search is not None
        for step in self.search:
            self._apply(step)
        self.path_shown = len(self.path)
        self.state = FINISHED

    def _after_change(self) -> None:
        """Called after the grid or settings changed."""
        if self.state == FINISHED:
            self.solve_instantly()  # live update of a finished result
        elif self.state != IDLE:
            self.clear_search()

    # ------------------------------------------------------------------ animation
    def _apply(self, step: Step) -> None:
        if step.kind == VISIT:
            self.frontier.discard(step.node)
            self.visited.add(step.node)
        elif step.kind == FRONTIER:
            self.frontier.add(step.node)
        elif step.kind == DONE:
            self.path = step.path or []
            self.search = None
            self.state = TRACING if self.path else FINISHED

    def update(self) -> None:
        if self.state == SEARCHING and self.search is not None:
            for _ in range(SPEEDS[self.speed_index]):
                step = next(self.search, None)
                if step is None:
                    self.state = FINISHED
                    break
                self._apply(step)
                if self.state != SEARCHING:
                    break
        elif self.state == TRACING:
            self.path_shown += max(1, SPEEDS[self.speed_index] // 5)
            if self.path_shown >= len(self.path):
                self.path_shown = len(self.path)
                self.state = FINISHED

    # ------------------------------------------------------------------ input
    def cell_at(self, pos: tuple[int, int]) -> Optional[Node]:
        x, y = pos
        if 0 <= x < self.grid_px[0] and 0 <= y < self.grid_px[1]:
            return (x // self.cell, y // self.cell)
        return None

    def _edit(self, node: Node) -> None:
        changed = False
        if self.drag_mode == "start":
            changed = self.grid.move_start(node)
        elif self.drag_mode == "goal":
            changed = self.grid.move_goal(node)
        elif self.drag_mode == "paint":
            if self.brush == "wall":
                changed = node not in self.grid.walls and self.grid.set_wall(node)
            else:
                changed = self.grid.weights.get(node) != DEFAULT_WEIGHT and self.grid.set_weight(node)
        elif self.drag_mode == "erase":
            changed = self.grid.clear_cell(node)
        if changed:
            self._after_change()

    def _place_endpoint(self, which: str) -> None:
        node = self.cell_at(pygame.mouse.get_pos())
        if node is None:
            return
        self.grid.walls.discard(node)
        moved = self.grid.move_start(node) if which == "start" else self.grid.move_goal(node)
        if moved:
            self._after_change()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            node = self.cell_at(event.pos)
            if node is None:
                if event.button == 1:
                    for button in self.buttons:
                        if button.handle_click(event.pos):
                            break
                return
            if event.button == 1:
                if node == self.grid.start:
                    self.drag_mode = "start"
                elif node == self.grid.goal:
                    self.drag_mode = "goal"
                else:
                    self.drag_mode = "paint"
            else:
                self.drag_mode = "erase"
            self.last_cell = node
            self._edit(node)
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.drag_mode = None
            self.last_cell = None
        elif event.type == pygame.MOUSEMOTION and self.drag_mode:
            node = self.cell_at(event.pos)
            if node is None or node == self.last_cell:
                return
            cells = [node] if self.drag_mode in ("start", "goal") or self.last_cell is None \
                else line_cells(self.last_cell, node)[1:]
            for cell in cells:
                self._edit(cell)
            self.last_cell = node

    def _handle_key(self, event: pygame.event.Event) -> None:
        key = event.key
        if pygame.K_1 <= key < pygame.K_1 + len(ALGORITHMS):
            self.select_algorithm(key - pygame.K_1)
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            self.start_search()
        elif key == pygame.K_c:
            self.clear_search()
        elif key == pygame.K_x:
            self.clear_walls()
        elif key == pygame.K_m:
            self.generate_maze()
        elif key == pygame.K_r:
            self.generate_random_walls()
        elif key == pygame.K_t:
            self.generate_random_weights()
        elif key == pygame.K_w:
            self.toggle_brush()
        elif key == pygame.K_d:
            self.toggle_diagonal()
        elif key == pygame.K_s:
            self._place_endpoint("start")
        elif key == pygame.K_g:
            self._place_endpoint("goal")
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.change_speed(1)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.change_speed(-1)
        elif key == pygame.K_ESCAPE:
            self.running = False

    # ------------------------------------------------------------------ drawing
    def draw(self) -> None:
        self.screen.fill(ui.BG)
        self._draw_grid()
        self._draw_panel()
        pygame.display.flip()

    def _draw_grid(self) -> None:
        cs = self.cell
        path_cells = set(self.path[: self.path_shown])
        for c in range(self.grid.cols):
            for r in range(self.grid.rows):
                node = (c, r)
                if node in self.grid.walls:
                    colour = ui.WALL
                elif node in path_cells:
                    colour = ui.PATH
                elif node in self.frontier:
                    colour = ui.FRONTIER
                elif node in self.visited:
                    colour = ui.VISITED
                elif node in self.grid.weights:
                    colour = ui.WEIGHT
                else:
                    colour = ui.EMPTY
                if node in self.grid.weights and colour in (ui.VISITED, ui.FRONTIER, ui.PATH):
                    colour = ui.blend(colour, ui.WEIGHT, 0.4)
                rect = pygame.Rect(c * cs, r * cs, cs, cs)
                pygame.draw.rect(self.screen, colour, rect)
                if node in self.grid.weights and node not in self.grid.walls:
                    label = self.fonts.cell.render(str(self.grid.weights[node]), True, (90, 60, 35))
                    self.screen.blit(label, label.get_rect(center=rect.center))
        # grid lines
        for c in range(self.grid.cols + 1):
            pygame.draw.line(self.screen, ui.GRID_LINE, (c * cs, 0), (c * cs, self.grid_px[1]))
        for r in range(self.grid.rows + 1):
            pygame.draw.line(self.screen, ui.GRID_LINE, (0, r * cs), (self.grid_px[0], r * cs))
        # path line
        shown = self.path[: self.path_shown]
        if len(shown) > 1:
            points = [(c * cs + cs // 2, r * cs + cs // 2) for c, r in shown]
            pygame.draw.lines(self.screen, (200, 140, 0), False, points, 3)
        # start / goal
        for node, colour in ((self.grid.start, ui.START), (self.grid.goal, ui.GOAL)):
            rect = pygame.Rect(node[0] * cs + 2, node[1] * cs + 2, cs - 4, cs - 4)
            pygame.draw.rect(self.screen, colour, rect, border_radius=5)
            letter = "S" if node == self.grid.start else "G"
            img = self.fonts.normal.render(letter, True, (255, 255, 255))
            self.screen.blit(img, img.get_rect(center=rect.center))

    def _draw_panel(self) -> None:
        x0 = self.grid_px[0]
        pygame.draw.rect(self.screen, ui.PANEL_BG, (x0, 0, PANEL_WIDTH, self.grid_px[1]))
        x = x0 + 15
        ui.draw_text(self.screen, self.fonts.title, "Path-Finding", (x, 16), ui.TEXT)
        ui.draw_text(self.screen, self.fonts.small, "ALGORITHM", (x, self.algo_label_y), ui.TEXT_DIM)
        ui.draw_text(self.screen, self.fonts.small, "ACTIONS", (x, self.actions_label_y), ui.TEXT_DIM)
        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(self.screen, self.fonts.small, mouse)

        y = self.stats_y
        y = ui.draw_text(self.screen, self.fonts.small, "STATS", (x, y), ui.TEXT_DIM)
        info = ALGORITHMS[self.algo_index]
        notes = []
        notes.append("weighted" if info.weighted else "ignores weights")
        notes.append("optimal" if info.shortest else "not optimal")
        y = ui.draw_text(self.screen, self.fonts.small, ", ".join(notes), (x, y), ui.TEXT_DIM)
        visited = len(self.visited)
        if self.result is None:
            lines = ["Press Space to run"]
        elif self.state == SEARCHING:
            lines = [f"Searching...  visited {visited}"]
        elif self.result.found:
            lines = [
                f"Visited nodes: {self.result.visited}",
                f"Path length: {self.result.length} moves",
                f"Path cost: {self.result.cost:.1f}",
                f"Compute time: {self.result.elapsed_ms:.2f} ms",
            ]
        else:
            lines = [f"Visited nodes: {self.result.visited}", "No path found!",
                     f"Compute time: {self.result.elapsed_ms:.2f} ms"]
        for line in lines:
            y = ui.draw_text(self.screen, self.fonts.normal, line, (x, y))
        y += 2
        settings = (f"Speed: {SPEED_NAMES[self.speed_index]}   "
                    f"Brush: {self.brush}   Diag: {'on' if self.diagonal else 'off'}")
        y = ui.draw_text(self.screen, self.fonts.small, settings, (x, y), ui.TEXT_DIM)
        y += 4
        y = ui.draw_legend(self.screen, self.fonts.small, x, y)
        hints = ["L-drag: draw  R-drag: erase", "Drag S/G (or keys S/G) to move"]
        for hint in hints:
            y = ui.draw_text(self.screen, self.fonts.small, hint, (x, y), ui.TEXT_DIM)

    # ------------------------------------------------------------------ main loop
    def step_frame(self) -> None:
        for event in pygame.event.get():
            self.handle_event(event)
        self.update()
        self.draw()

    def run(self) -> None:
        while self.running:
            self.step_frame()
            self.clock.tick(FPS)
        pygame.quit()
