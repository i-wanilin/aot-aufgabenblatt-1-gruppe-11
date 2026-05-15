"""Three pheromone channels backed by numpy arrays.

Channels:
- nest: dropped by outbound ants (carrying nothing); used by returners.
- food: dropped by returning ants (carrying food); used by outbound ants.
- neg : dropped on the way back along a path where food was expected but
        not found. Dampens cells on exhausted trails.

Deposit amount on a single cell uses a decreasing-rate model:
    amount = deposit_initial * decay_per_step^k
where k = number of ticks since the current trip started (last nest visit
for outbound, last food pickup for returners).

Evaporation is multiplicative per tick: x *= (1 - rate), values below
min_level are clamped to 0 to avoid float drift.
"""
from __future__ import annotations

import numpy as np


CHANNELS = ("nest", "food", "neg")


def _bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        cells.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x += sx
        if e2 <= dx:
            err += dx; y += sy
    return cells


class PheromoneField:
    def __init__(self, height: int, width: int, cfg: dict):
        self.h, self.w = height, width
        self.nest = np.zeros((height, width), dtype=np.float32)
        self.food = np.zeros((height, width), dtype=np.float32)
        self.neg = np.zeros((height, width), dtype=np.float32)

        ph = cfg["pheromones"]
        self.evap: float = float(ph["evaporation"])
        self.neg_evap: float = float(ph.get("neg_evap_rate", self.evap))
        self.deposit_initial: float = float(ph["deposit_initial"])
        self.decay_per_step: float = float(ph["decay_per_step"])
        self.min_level: float = float(ph.get("min_level", 0.0))
        self.neg_deposit: float = float(ph.get("neg_deposit", 0.0))
        self.expect_threshold: float = float(ph.get("expect_food_threshold", 0.0))
        self.neg_weight: float = float(ph.get("neg_weight", 1.0))

        ws = cfg.get("warm_start", {}) or {}
        for trail in ws.get("trails", []):
            self.get_channel(trail["channel"])[trail["y"], trail["x"]] += float(trail["level"])
        for line in ws.get("lines", []):
            x0, y0 = line["start"]
            x1, y1 = line["end"]
            l0 = float(line["level_at_start"])
            l1 = float(line["level_at_end"])
            cells = _bresenham(int(x0), int(y0), int(x1), int(y1))
            if not cells:
                continue
            field = self.get_channel(line["channel"])
            for i, (cx, cy) in enumerate(cells):
                t = i / max(1, len(cells) - 1)
                field[cy, cx] += l0 + (l1 - l0) * t

    def get_channel(self, name: str) -> np.ndarray:
        if name == "nest":
            return self.nest
        if name == "food":
            return self.food
        if name == "neg":
            return self.neg
        raise ValueError(f"unknown pheromone channel: {name}")

    def deposit_step(self, channel: str, x: int, y: int, step_k: int) -> float:
        """Deposit pheromone with decreasing strength at step k since trip start."""
        amount = self.deposit_initial * (self.decay_per_step ** step_k)
        if amount < self.min_level:
            return 0.0
        self.get_channel(channel)[y, x] += amount
        return amount

    def deposit_neg(self, x: int, y: int) -> float:
        if self.neg_deposit <= 0.0:
            return 0.0
        self.neg[y, x] += self.neg_deposit
        return self.neg_deposit

    def evaporate(self) -> None:
        self.nest *= (1.0 - self.evap)
        self.food *= (1.0 - self.evap)
        self.neg *= (1.0 - self.neg_evap)
        if self.min_level > 0.0:
            self.nest[self.nest < self.min_level] = 0.0
            self.food[self.food < self.min_level] = 0.0
            self.neg[self.neg < self.min_level] = 0.0

    def zero_all(self) -> None:
        """Used during the pheromone_outage window."""
        self.nest[:] = 0.0
        self.food[:] = 0.0
        self.neg[:] = 0.0

    def sums(self) -> dict:
        return {
            "nest": float(self.nest.sum()),
            "food": float(self.food.sum()),
            "neg": float(self.neg.sum()),
        }
