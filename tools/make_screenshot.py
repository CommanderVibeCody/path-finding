"""Render docs/screenshot.png headlessly: ``python tools/make_screenshot.py``."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame  # noqa: E402

from pathfinding.app import App  # noqa: E402
from pathfinding.maze import random_walls, random_weights  # noqa: E402


def main(out: str = "docs/screenshot.png", seed: int = 7) -> None:
    app = App()
    app.grid.start, app.grid.goal = (2, 3), (32, 25)
    random_walls(app.grid, density=0.27, seed=seed)
    random_weights(app.grid, density=0.08, seed=seed)
    app.select_algorithm(0)  # A*
    app.solve_instantly()
    if not app.path:
        raise SystemExit(f"seed {seed} produced an unsolvable grid, try another one")
    app.draw()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pygame.image.save(app.screen, out)
    print(f"saved {out} ({app.result.visited} visited, {app.result.length} moves)")
    pygame.quit()


if __name__ == "__main__":
    main()
