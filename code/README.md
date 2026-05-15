# Ant-colony simulator — AOT Aufgabenblatt 1 (Gruppe 11)

Reactive multi-agent ant colony in a 2D grid world. Implements the design
laid out in `../aufgabenblatt-1-projektskizze/projektskizze.md`.

## Requirements

- Python 3.10 or newer
- `numpy`, `matplotlib`, `jsonschema`

```bash
python3 -m venv .venv
.venv/bin/pip install numpy matplotlib jsonschema
```

## Layout

```
code/
├── sim/                       # the simulator package
│   ├── __main__.py            # CLI entry point
│   ├── config.py              # JSON load + schema validation
│   ├── world.py               # GridWorld, nests, food sources
│   ├── pheromones.py          # 3-channel pheromone field (nest/food/neg)
│   ├── agent.py               # AntAgent (sense -> reason -> act)
│   ├── manager.py             # SimulationManager (tick loop)
│   ├── logger.py              # JSONL events + per-source counters
│   └── world.schema.json      # JSON-schema for the model file
├── experiments/               # the experiment configurations
│   ├── experiment_1_close.json
│   ├── experiment_1_mid.json
│   ├── experiment_1_far.json
│   ├── experiment_1_close_n40.json
│   ├── experiment_1_mid_n40.json
│   ├── experiment_1_far_n40.json
│   ├── experiment_2_coldstart.json
│   ├── experiment_2_warmstart.json
│   ├── experiment_2_outage.json
│   ├── experiment_3_evap_low.json
│   ├── experiment_3_evap_mid.json
│   ├── experiment_3_evap_high.json
│   └── experiment_3_blockade.json
└── plot.py                    # post-hoc plots from events.jsonl
```

## Running one experiment

```bash
.venv/bin/python -m sim --config experiments/experiment_1_mid.json
```

This produces `runs/<config-stem>_seed<N>_<timestamp>/` containing:

| file                  | what it is                                            |
| --------------------- | ----------------------------------------------------- |
| `events.jsonl`        | one line per logged tick: `tick`, `food_in_nest`, per-source delivered + remaining, `n_alive`, `n_carrying`, `mean_energy`, pheromone sums, `conflicts` (interval total), `outage` flag, `dynamic_blocked_cells` count |
| `header.json`         | run metadata: seed, comment, grid, nests, food positions |
| `summary.json`        | totals + `t_first` per source, deaths, final tick     |
| `capacity.npy`        | initial obstacle/capacity grid (post-static, pre-dynamic) — used by `plot.py` as a fallback mask |
| `snapshots/tick_*.npz`| pheromone field snapshots (`nest`, `food`, `neg`) plus the per-tick `capacity` so heatmaps reflect dynamic-obstacle state |

To force a different seed without editing the JSON:

```bash
.venv/bin/python -m sim --config experiments/experiment_1_mid.json --seed 42
```

To override the output root directory:

```bash
.venv/bin/python -m sim --config experiments/experiment_1_mid.json --output-dir /tmp/out
```

## Running all experiments

A simple shell loop covers all configs with three seeds each:

```bash
for cfg in experiments/experiment_*.json; do
  for seed in 1 2 3; do
    .venv/bin/python -m sim --config "$cfg" --seed "$seed" --output-dir runs --quiet
  done
done
```

The default `output_dir` is `runs/`. Each run lands in its own subdirectory
keyed by config stem + seed + timestamp, so reruns do not overwrite.

## Plotting

```bash
.venv/bin/python plot.py runs/experiment_1_close_seed1_*/ \
                         runs/experiment_1_mid_seed1_*/ \
                         runs/experiment_1_far_seed1_*/ \
                         --out plots/exp1_n20 --window 200
```

All positional run-dirs get overlaid on the comparative plots and each gets
its own set of heatmaps. Plots produced per output folder:

- `cumulative.png` — cumulative food in nest, per source, per run (one line per source per run)
- `rate.png` — rolling delivery rate `r(t)` (`--window` ticks, default 50; we use 200 in practice). Pheromone outages are shaded gray; dynamic-obstacle windows are shaded moccasin.
- `t_first.png` — bar chart of the tick of the first delivery per source. Never-delivered sources are rendered with an "n/a" annotation.
- `heatmap_{food,nest,neg}__<run_name>.png` — pheromone heatmaps at 6 evenly-spaced ticks per channel per run. Math-paper grid overlay, **N** marks the nest, **F** (or F₀, F₁, …) the active food sources, **X** (or X₀, X₁, …) depleted sources, white squares are obstacles (both static and dynamic at the snapshot's tick).
- `summary.csv` — one row per run with the run-level metrics.

The repo is organised into 5 result folders, one per "rubric experiment":

| folder                 | overlaid runs                                          |
| ---------------------- | ------------------------------------------------------ |
| `plots/exp1_n20/`      | 3 distance variants at N=20                            |
| `plots/exp1_n40/`      | 3 distance variants at N=40                            |
| `plots/exp1_compare/`  | mid @ N=20 vs mid @ N=40 — isolates the population effect |
| `plots/exp2/`          | coldstart + warmstart + outage                         |
| `plots/exp3/`          | evap_low + evap_mid + evap_high + blockade             |

## Configuration reference

Configs are validated against `sim/world.schema.json`. The top-level keys:

| key             | meaning                                                                  |
| --------------- | ------------------------------------------------------------------------ |
| `seed`          | RNG seed (overridden by `--seed`)                                        |
| `grid`          | `width`, `height`, `default_capacity`                                    |
| `obstacles`     | list of rectangles with capacity 0                                       |
| `dynamic_obstacles` | rectangles that block their cells only between `appears_at` and `disappears_at`; any ant caught underneath when an obstacle appears is killed |
| `nests`         | list of `{x, y, capacity}` — at least one                                |
| `food`          | list of `{x, y, amount}` — at least one                                  |
| `agents`        | `count`, `spawn` (`nest`/`random`), `initial_energy`, `energy_max`       |
| `costs`         | per-action energy cost (informational; per-tick=1 is the rubric rule)    |
| `pheromones`    | `evaporation`, `deposit_initial`, `decay_per_step`, neg-channel knobs    |
| `movement`      | `epsilon` (random-move probability), `w_food`, `w_nest`                  |
| `warm_start`    | `trails` (cell list) and/or `lines` (start→end with linear gradient)     |
| `perturbations` | `pheromone_outage = { start_tick, length }` for Exp 2 outage             |
| `termination`   | `max_ticks`, `stop_when_food_zero` (also waits for in-flight carriers)   |
| `logging`       | `metrics_every`, `snapshot_every`, `output_dir`                          |

`comment` is a free-form string describing the experiment (required by the
rubric — PDF p.2).
