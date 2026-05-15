"""AntAgent — reactive ant with Sense → Reason → Act.

The agent emits an ActionRequest each tick; the manager validates and
applies it (FCFS conflict resolution lives in the manager).

State the agent keeps:
- position (x, y)
- carrying (bool) + carried_from_source id
- energy
- step_k: ticks since the current trip started, used by the
  decreasing-rate pheromone deposit (deposit = initial * decay^k)
- neg_active: set when an outbound ant lands on a cell whose food
  pheromone exceeded the expect threshold but had no food. While the
  flag is on, the ant drops negative pheromone on the cell it most
  recently left (path[-1]) as it continues to wander.
  Note: this is a simplification of the Skizze §5.1 description, which
  spoke of dropping neg "auf dem Rückweg". We do not implement a
  separate retreat-to-nest mode; instead the frustrated ant tags
  cells behind itself while still outbound. The aggregate effect is
  the same — cells on misleading trails accumulate neg-pheromone —
  but the timing differs. Documented in Projektdokumentation §"Anpassungen".
- path: bounded deque of the last K visited cells. Used for cycle
  avoidance in scoring and for picking the cell to tag with neg.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .pheromones import PheromoneField
    from .world import GridWorld


PATH_HISTORY = 32  # cells of recent-position memory per ant


@dataclass
class ActionRequest:
    agent_id: int
    kind: str       # "move" | "pickup" | "drop" | "noop"
    target: tuple[int, int] | None = None
    deposit_channel: str | None = None
    deposit_step_k: int | None = None


@dataclass
class Perception:
    x: int
    y: int
    on_nest: bool
    food_here: int
    food_source_id: int | None
    neighbours: list[tuple[int, int]]
    nest_levels: list[float]
    food_levels: list[float]
    neg_levels: list[float]


class AntAgent:
    def __init__(self, agent_id: int, x: int, y: int,
                 initial_energy: int, energy_max: int):
        self.agent_id = agent_id
        self.x = x
        self.y = y
        self.energy = initial_energy
        self.energy_max = energy_max
        self.carrying = False
        self.carried_from_source: int | None = None
        self.alive = True

        self.step_k = 0
        self.neg_active = False
        self.path: deque[tuple[int, int]] = deque(maxlen=PATH_HISTORY)

    # ------------------------------------------------------------------ sense
    def sense(self, world: "GridWorld", ph: "PheromoneField") -> Perception:
        ns = world.neighbours(self.x, self.y)
        food = world.food_at(self.x, self.y)
        return Perception(
            x=self.x, y=self.y,
            on_nest=world.is_nest(self.x, self.y),
            food_here=food.remaining if food else 0,
            food_source_id=food.source_id if food else None,
            neighbours=ns,
            nest_levels=[float(ph.nest[y, x]) for x, y in ns],
            food_levels=[float(ph.food[y, x]) for x, y in ns],
            neg_levels=[float(ph.neg[y, x]) for x, y in ns],
        )

    # ------------------------------------------------------------------ reason
    def decide(self, perc: Perception, move_cfg: dict, ph_cfg: dict,
               rng: np.random.Generator) -> ActionRequest:
        # PDF algorithm steps 4 and 5 are explicit actions.
        if self.carrying and perc.on_nest:
            return ActionRequest(self.agent_id, "drop")
        if (not self.carrying) and perc.food_here > 0:
            return ActionRequest(self.agent_id, "pickup")

        if not perc.neighbours:
            return ActionRequest(self.agent_id, "noop")

        epsilon = float(move_cfg.get("epsilon", 0.05))
        w_food = float(move_cfg.get("w_food", 1.0))
        w_nest = float(move_cfg.get("w_nest", 1.0))
        neg_w = float(ph_cfg.get("neg_weight", 1.0))

        if rng.random() < epsilon:
            target = perc.neighbours[int(rng.integers(0, len(perc.neighbours)))]
            return ActionRequest(self.agent_id, "move", target=target,
                                 deposit_channel=self._deposit_channel(),
                                 deposit_step_k=self.step_k)

        # Score each walkable neighbour. Outbound ant climbs the food gradient,
        # returner climbs the nest gradient. Both channels are dampened by neg.
        scores = []
        for i, (nx, ny) in enumerate(perc.neighbours):
            attractor = (w_food * perc.food_levels[i]
                         if not self.carrying
                         else w_nest * perc.nest_levels[i])
            s = attractor - neg_w * perc.neg_levels[i]
            if (nx, ny) in self.path:
                s -= 0.5  # cycle-avoidance penalty
            scores.append(s)

        s = np.array(scores, dtype=np.float64)
        # softmax; uniform if all scores tied. Subtracting s.max() is the
        # standard numerical-stability trick — it keeps the largest exponent
        # at exp(0)=1 instead of exp(big number)=inf.
        if np.all(s == s[0]):
            probs = np.full_like(s, 1.0 / len(s))
        else:
            z = s - s.max()
            probs = np.exp(z)
            probs /= probs.sum()
        idx = int(rng.choice(len(perc.neighbours), p=probs))
        target = perc.neighbours[idx]
        return ActionRequest(self.agent_id, "move", target=target,
                             deposit_channel=self._deposit_channel(),
                             deposit_step_k=self.step_k)

    def _deposit_channel(self) -> str:
        # Outbound (no food) → drop NEST pheromone (so returners use it).
        # Returning (carrying) → drop FOOD pheromone (so seekers use it).
        return "food" if self.carrying else "nest"

    def reset_trip(self) -> None:
        """Called when entering nest (without food) or picking up food."""
        self.step_k = 0
        self.neg_active = False
        self.path.clear()
