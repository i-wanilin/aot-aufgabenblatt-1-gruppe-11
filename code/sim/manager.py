"""SimulationManager: orchestrates one run.

Tick structure (Skizze §5):
  1. apply_actions    — replay the actions decided last tick (FCFS by agent id)
  2. sense + decide   — each living agent perceives + emits next action
  3. evaporate        — pheromone fields decay one step
  4. log_and_advance  — write metrics, tick++

On the very first tick there is no "previous action" queue, so step 1 is
a no-op. Movement, energy cost, food pickup/drop and pheromone deposit
all happen inside step 1.

Death rule: energy hits 0 → agent removed from the active set. If it was
carrying, the food is dropped on the cell (becomes a new food source of
size 1 at that cell, conceptually — but to keep the schema simple we
just credit it back to its original source).

Conflict resolution: when two agents want to move into the same cell on
the same tick, the one with the lower agent_id wins; later contenders
implicitly noop and pay only the move energy if the move was nominally
legal (cost goes to "conflicts" counter instead — they pay nothing).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from .agent import ActionRequest, AntAgent, Perception
from .pheromones import PheromoneField
from .world import GridWorld


class SimulationManager:
    def __init__(self, cfg: dict, logger):
        self.cfg = cfg
        self.logger = logger
        self.rng = np.random.default_rng(int(cfg["seed"]))

        self.world = GridWorld(cfg)
        self.pheromones = PheromoneField(self.world.height, self.world.width, cfg)

        agents_cfg = cfg["agents"]
        n = int(agents_cfg["count"])
        initial_energy = int(agents_cfg["initial_energy"])
        energy_max = int(agents_cfg.get("energy_max", initial_energy))
        spawn = agents_cfg.get("spawn", "nest")
        # When spawn="nest", verify the colony fits in the declared nest
        # capacity. _spawn_position then iterates nests respecting per-cell
        # capacity instead of stacking everyone onto nests[0].
        if spawn == "nest":
            total_nest_cap = sum(net.capacity for net in self.world.nests)
            if total_nest_cap < n:
                raise ValueError(
                    f"agents.count={n} exceeds total nest capacity ({total_nest_cap}). "
                    f"Either raise nest capacities or use spawn='random'."
                )

        self.agents: list[AntAgent] = []
        for i in range(n):
            x, y = self._spawn_position(spawn)
            a = AntAgent(agent_id=i, x=x, y=y,
                         initial_energy=initial_energy, energy_max=energy_max)
            # Spawning ON a nest cell counts as being at the nest, so the
            # PDF refresh rule applies: start with full energy. Ants spawned
            # elsewhere (spawn=random) use initial_energy as given.
            if self.world.is_nest(x, y):
                a.energy = energy_max
            self.world.occupancy[y, x] += 1
            self.agents.append(a)

        self.move_cfg = cfg.get("movement", {}) or {}

        term = cfg["termination"]
        self.max_ticks = int(term["max_ticks"])
        self.stop_when_food_zero = bool(term.get("stop_when_food_zero", False))

        pert = cfg.get("perturbations", {}) or {}
        self.outage = pert.get("pheromone_outage")  # dict with start_tick, length

        # Expand each dynamic_obstacles entry into a sorted appear/disappear
        # event list. Each event carries the rectangle's cell list. We sort
        # by (tick, kind=appear-before-disappear) so simultaneous toggles at
        # the same tick are handled in a stable order.
        self._events: list[tuple[int, str, list[tuple[int, int]]]] = []
        for ob in cfg.get("dynamic_obstacles", []):
            x0, y0 = int(ob["x"]), int(ob["y"])
            ow, oh = int(ob.get("w", 1)), int(ob.get("h", 1))
            cells = [(x, y) for y in range(y0, y0 + oh) for x in range(x0, x0 + ow)]
            self._events.append((int(ob["appears_at"]), "appear", cells))
            self._events.append((int(ob["disappears_at"]), "disappear", cells))
        # appear before disappear at the same tick
        self._events.sort(key=lambda e: (e[0], 0 if e[1] == "appear" else 1))
        self._next_event_idx = 0

        self.tick = 0
        self.food_in_nest = 0
        self.food_in_nest_per_source: dict[int, int] = {s.source_id: 0 for s in self.world.food_sources}
        self.t_first: dict[int, int | None] = {s.source_id: None for s in self.world.food_sources}
        self.deaths = 0
        self.pending_actions: list[ActionRequest] = []
        # Accumulated across ticks; the logger reads it and resets to 0 each
        # time it writes a row. With metrics_every=1 that's per-tick;
        # with metrics_every>1 it's the interval total.
        self.conflicts_since_log = 0

    # ------------------------------------------------------------------ spawn
    def _spawn_position(self, spawn: str) -> tuple[int, int]:
        if spawn == "random":
            for _ in range(1000):
                x = int(self.rng.integers(0, self.world.width))
                y = int(self.rng.integers(0, self.world.height))
                if self.world.has_room(x, y):
                    return x, y
            raise RuntimeError("could not place agent randomly")
        # spawn="nest": pick the first nest with room left under its capacity.
        # The pre-flight capacity check in __init__ guarantees at least one
        # such cell exists, but the loop tolerates per-nest exhaustion too.
        for net in self.world.nests:
            if self.world.occupancy[net.y, net.x] < net.capacity:
                return net.x, net.y
        raise RuntimeError(
            "no nest cell has remaining capacity (this should have been caught upfront)"
        )

    # ------------------------------------------------------------------ run
    def run(self) -> None:
        self.logger.header(self.cfg, self.world)
        while True:
            self._tick()
            if self.tick >= self.max_ticks:
                break
            if (self.stop_when_food_zero
                    and self.world.total_food_remaining() == 0
                    and self.n_carrying() == 0):
                # Only stop once all food has been delivered too — otherwise
                # the run ends while ants are still in transit and their
                # items never get credited.
                break

    # ------------------------------------------------------------------ tick
    def _tick(self) -> None:
        # Increment first so every "is this tick in the outage window?" check
        # (both inside the pheromone-update branch below AND inside the
        # logger) reads the same value. Convention: after `self.tick += 1`,
        # self.tick == N means "we are now executing the Nth tick".
        self.tick += 1

        # Apply any dynamic-obstacle events scheduled for this tick BEFORE
        # agents do anything: an obstacle that appears on a cell kills any
        # ants standing there before they get to move this tick.
        self._apply_dynamic_obstacle_events()

        self.conflicts_since_log += self._apply_actions(self.pending_actions)
        self.pending_actions = []

        # decide next actions for living agents
        for a in self.agents:
            if not a.alive:
                continue
            # energy tick-cost first, then the agent decides
            a.energy -= 1
            if a.energy <= 0:
                self._kill(a)
                continue
            perc = a.sense(self.world, self.pheromones)
            self.pending_actions.append(
                a.decide(perc, self.move_cfg, self.cfg["pheromones"], self.rng)
            )

        # pheromone update — but during an outage we zero everything out
        if self._in_outage():
            self.pheromones.zero_all()
        else:
            self.pheromones.evaporate()

        self.logger.tick(self)

    def _in_outage(self) -> bool:
        if not self.outage:
            return False
        s = int(self.outage["start_tick"])
        L = int(self.outage["length"])
        return s <= self.tick < s + L

    # ----------------------------------------------------- dynamic obstacles
    def _apply_dynamic_obstacle_events(self) -> None:
        """Drain any events scheduled for the current tick.

        appear   → for each cell: bump blocker counter, set capacity=0,
                   kill any ants currently on the cell.
        disappear → for each cell: drop blocker counter; if it returns to 0,
                    restore capacity from base_capacity.
        """
        while (self._next_event_idx < len(self._events)
               and self._events[self._next_event_idx][0] <= self.tick):
            _, kind, cells = self._events[self._next_event_idx]
            self._next_event_idx += 1
            if kind == "appear":
                for (x, y) in cells:
                    self.world.dynamic_blocker_count[y, x] += 1
                    self.world.capacity[y, x] = 0
                    # Kill any ant standing on a now-blocked cell.
                    for a in self.agents:
                        if a.alive and a.x == x and a.y == y:
                            self._kill(a)
            else:  # disappear
                for (x, y) in cells:
                    self.world.dynamic_blocker_count[y, x] -= 1
                    if self.world.dynamic_blocker_count[y, x] == 0:
                        self.world.capacity[y, x] = self.world.base_capacity[y, x]

    # ------------------------------------------------------------------ apply
    def _apply_actions(self, actions: list[ActionRequest]) -> int:
        conflicts = 0
        # FCFS by agent_id — Skizze §4.3
        for req in sorted(actions, key=lambda r: r.agent_id):
            a = self.agents[req.agent_id]
            if not a.alive:
                continue
            if req.kind == "move":
                conflicts += self._do_move(a, req)
            elif req.kind == "pickup":
                self._do_pickup(a)
            elif req.kind == "drop":
                self._do_drop(a)
            # noop: nothing
        return conflicts

    def _do_move(self, a: AntAgent, req: ActionRequest) -> int:
        tx, ty = req.target  # type: ignore[misc]
        if not self.world.has_room(tx, ty):
            # blocked → counts as conflict if obstacle is full (vs. obstacle-tile)
            return 1 if self.world.is_walkable(tx, ty) else 0

        # leave current cell
        self.world.occupancy[a.y, a.x] -= 1
        a.path.append((a.x, a.y))
        a.x, a.y = tx, ty
        self.world.occupancy[ty, tx] += 1
        a.step_k += 1
        # Energy is deducted exactly once per tick in `_tick` (PDF rule:
        # 1 Energieeinheit pro Zeitschritt). `costs.*` in the config is
        # currently informational only — it carries the rubric's bookkeeping
        # of which action consumed the tick but does not re-deduct.

        # pheromone deposit at the new cell
        if not self._in_outage() and req.deposit_channel is not None:
            self.pheromones.deposit_step(req.deposit_channel, tx, ty, int(req.deposit_step_k or 0))

        # neg deposition: if outbound and current cell had food expectation
        # but we don't actually carry food yet, mark for negative tagging on
        # the return. Simpler operationalisation: any time a CARRYING ant
        # walks back, it does NOT do neg. Any time an outbound ant arrives
        # at a cell where food_pheromone > threshold AND that cell has no
        # food, flip neg_active on. Then on subsequent OUTBOUND steps drop
        # neg behind us (i.e. on the cell we just left).
        if not a.carrying:
            food_here_now = self.world.food_at(tx, ty)
            if (food_here_now is None
                    and self.pheromones.food[ty, tx] > self.pheromones.expect_threshold):
                a.neg_active = True
            if a.neg_active and not self._in_outage():
                # tag the cell we just LEFT (it's already in path[-1] thanks to
                # the append above) — that's where the misleading trail led.
                if a.path:
                    px, py = a.path[-1]
                    self.pheromones.deposit_neg(px, py)

        # implicit energy refresh on entering nest or food cell
        if self.world.is_nest(tx, ty):
            a.energy = a.energy_max
            # arriving at nest resets the outbound trip — even before drop,
            # because the drop happens next tick and we want step_k fresh.
            # We DO NOT reset if carrying — drop comes first to credit food.
            if not a.carrying:
                a.reset_trip()
        elif self.world.food_at(tx, ty) is not None:
            a.energy = a.energy_max

        if a.energy <= 0:
            self._kill(a)
        return 0

    def _do_pickup(self, a: AntAgent) -> None:
        if a.carrying:
            return
        src = self.world.food_at(a.x, a.y)
        if src is None or src.remaining <= 0:
            return
        src.remaining -= 1
        a.carrying = True
        a.carried_from_source = src.source_id
        a.reset_trip()  # start the return trip fresh
        # implicit energy refresh on food cell
        a.energy = a.energy_max

    def _do_drop(self, a: AntAgent) -> None:
        if not a.carrying:
            return
        if not self.world.is_nest(a.x, a.y):
            return
        a.carrying = False
        sid = a.carried_from_source if a.carried_from_source is not None else -1
        self.food_in_nest += 1
        if sid in self.food_in_nest_per_source:
            self.food_in_nest_per_source[sid] += 1
            if self.t_first[sid] is None:
                self.t_first[sid] = self.tick
        a.carried_from_source = None
        a.reset_trip()
        a.energy = a.energy_max

    def _kill(self, a: AntAgent) -> None:
        if not a.alive:
            return
        a.alive = False
        self.deaths += 1
        self.world.occupancy[a.y, a.x] -= 1
        if a.carrying:
            # drop the carried food back to its source (counts as not-yet-delivered)
            sid = a.carried_from_source
            if sid is not None:
                for s in self.world.food_sources:
                    if s.source_id == sid:
                        s.remaining += 1
                        break

    # ------------------------------------------------------------------ summary
    def n_alive(self) -> int:
        return sum(1 for a in self.agents if a.alive)

    def n_carrying(self) -> int:
        return sum(1 for a in self.agents if a.alive and a.carrying)

    def mean_energy(self) -> float:
        es = [a.energy for a in self.agents if a.alive]
        return float(sum(es) / len(es)) if es else 0.0
