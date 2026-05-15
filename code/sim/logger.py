"""JSONL logger.

Writes per run:
- events.jsonl        — one line per (logged) tick with aggregate metrics
                        + per-source delivery counters.
- header.json         — config metadata + grid topology + nest/food positions.
- capacity.npy        — obstacle/capacity grid, used by plot.py for masks.
- snapshots/tick_*.npz — pheromone-field snapshots for heatmaps.
- summary.json        — totals + t_first per source, written on close().

Each event line is flushed so a crashed run still leaves usable data behind.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .manager import SimulationManager
    from .world import GridWorld


class JsonlLogger:
    def __init__(self, output_dir: str | Path, run_id: str,
                 metrics_every: int = 1, snapshot_every: int = 200):
        self.dir = Path(output_dir) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.dir / "events.jsonl"
        self.header_path = self.dir / "header.json"
        self.snap_dir = self.dir / "snapshots"
        self.snap_dir.mkdir(exist_ok=True)
        # On --run-id reuse, drop stale snapshots from the previous run.
        # Without this, plot.py picks up old tick_*.npz files alongside the
        # new ones and produces misleading heatmaps.
        for stale in self.snap_dir.glob("tick_*.npz"):
            stale.unlink()

        self.metrics_every = max(1, int(metrics_every))
        self.snapshot_every = max(1, int(snapshot_every))

        self._events_fh = self.events_path.open("w", encoding="utf-8")

    def header(self, cfg: dict, world: "GridWorld") -> None:
        h = {
            "schema_version": cfg.get("schema_version"),
            "seed": cfg.get("seed"),
            "comment": cfg.get("comment", ""),
            "grid": {"width": world.width, "height": world.height},
            "nests": [{"id": n.nest_id, "x": n.x, "y": n.y} for n in world.nests],
            "food": [
                {"id": s.source_id, "x": s.x, "y": s.y, "amount": s.initial_amount}
                for s in world.food_sources
            ],
        }
        self.header_path.write_text(json.dumps(h, indent=2), encoding="utf-8")
        np.save(self.dir / "capacity.npy", world.capacity)

    def tick(self, sm: "SimulationManager") -> None:
        if sm.tick % self.metrics_every != 0:
            self._maybe_snapshot(sm)
            return
        row = {
            "tick": sm.tick,
            "food_in_nest": sm.food_in_nest,
            "food_in_nest_per_source": {str(k): v for k, v in sm.food_in_nest_per_source.items()},
            "food_remaining_per_source": {
                str(s.source_id): s.remaining for s in sm.world.food_sources
            },
            "n_alive": sm.n_alive(),
            "n_carrying": sm.n_carrying(),
            "n_searching": sm.n_alive() - sm.n_carrying(),
            "deaths_total": sm.deaths,
            "mean_energy": sm.mean_energy(),
            "pheromones": sm.pheromones.sums(),
            "conflicts": sm.conflicts_since_log,
            "outage": sm._in_outage(),
            "dynamic_blocked_cells": int(sm.world.dynamic_blocker_count.sum()),
        }
        sm.conflicts_since_log = 0
        self._events_fh.write(json.dumps(row) + "\n")
        self._events_fh.flush()
        self._maybe_snapshot(sm)

    def _maybe_snapshot(self, sm: "SimulationManager") -> None:
        if sm.tick % self.snapshot_every != 0:
            return
        np.savez_compressed(
            self.snap_dir / f"tick_{sm.tick:05d}.npz",
            nest=sm.pheromones.nest, food=sm.pheromones.food, neg=sm.pheromones.neg,
            capacity=sm.world.capacity,
        )

    def close(self, sm: "SimulationManager | None" = None) -> None:
        if sm is not None:
            summary = {
                "final_tick": sm.tick,
                "food_in_nest": sm.food_in_nest,
                "food_in_nest_per_source": {str(k): v for k, v in sm.food_in_nest_per_source.items()},
                "t_first": {str(k): v for k, v in sm.t_first.items()},
                "deaths": sm.deaths,
                "n_alive_final": sm.n_alive(),
            }
            (self.dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        self._events_fh.close()
