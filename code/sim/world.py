"""GridWorld: capacity grid, obstacles, nests, food sources, occupancy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


@dataclass
class Nest:
    nest_id: int
    x: int
    y: int
    capacity: int


@dataclass
class FoodSource:
    source_id: int
    x: int
    y: int
    initial_amount: int
    remaining: int


class GridWorld:
    """Static topology (capacities, obstacles, nests, food) + dynamic occupancy.

    Coordinates: x = column (0..width-1), y = row (0..height-1).
    Internally we keep numpy arrays indexed as [y, x] for cache-friendly slicing
    of pheromone neighborhoods.
    """

    def __init__(self, cfg: dict):
        g = cfg["grid"]
        self.width: int = int(g["width"])
        self.height: int = int(g["height"])
        self.default_capacity: int = int(g["default_capacity"])

        self.capacity = np.full((self.height, self.width), self.default_capacity, dtype=np.int32)
        for ob in cfg.get("obstacles", []):
            x0, y0 = int(ob["x"]), int(ob["y"])
            w, h = int(ob.get("w", 1)), int(ob.get("h", 1))
            self.capacity[y0:y0 + h, x0:x0 + w] = 0

        self.nests: list[Nest] = []
        for i, n in enumerate(cfg.get("nests", [])):
            nid = int(n.get("id", i))
            self.nests.append(Nest(nest_id=nid, x=int(n["x"]), y=int(n["y"]),
                                   capacity=int(n.get("capacity", 9999))))
        # Force nest cells to be walkable with their declared capacity.
        for n in self.nests:
            self.capacity[n.y, n.x] = max(self.capacity[n.y, n.x], n.capacity)

        self.food_sources: list[FoodSource] = []
        for i, f in enumerate(cfg.get("food", [])):
            fid = int(f.get("id", i))
            self.food_sources.append(FoodSource(
                source_id=fid, x=int(f["x"]), y=int(f["y"]),
                initial_amount=int(f["amount"]), remaining=int(f["amount"]),
            ))

        # Snapshot of capacity AFTER static obstacles + nest forcing, but
        # BEFORE any dynamic obstacle modifies it. Used by the manager to
        # restore cells when a dynamic obstacle disappears.
        self.base_capacity = self.capacity.copy()
        # Per-cell counter of how many dynamic obstacles currently cover it.
        # Cell is dynamic-blocked iff dynamic_blocker_count[y, x] > 0.
        self.dynamic_blocker_count = np.zeros((self.height, self.width), dtype=np.int32)

        self.occupancy = np.zeros((self.height, self.width), dtype=np.int32)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return self.capacity[y, x] > 0

    def has_room(self, x: int, y: int) -> bool:
        return self.is_walkable(x, y) and self.occupancy[y, x] < self.capacity[y, x]

    def is_nest(self, x: int, y: int) -> bool:
        return any(n.x == x and n.y == y for n in self.nests)

    def food_at(self, x: int, y: int) -> FoodSource | None:
        for s in self.food_sources:
            if s.x == x and s.y == y and s.remaining > 0:
                return s
        return None

    def neighbours(self, x: int, y: int) -> list[tuple[int, int]]:
        # 4-connected (von Neumann). Skizze §3.1 commits to this choice; the
        # PDF allows 4 or 8 but we don't need diagonals.
        deltas = [(0, -1), (-1, 0), (1, 0), (0, 1)]
        return [(x + dx, y + dy) for dx, dy in deltas if self.is_walkable(x + dx, y + dy)]

    def total_food_remaining(self) -> int:
        return sum(s.remaining for s in self.food_sources)
