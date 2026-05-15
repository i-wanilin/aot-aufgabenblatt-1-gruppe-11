"""Post-hoc plots for one or more runs.

Usage:
    python plot.py path/to/run_dir [path/to/another_run ...]
        --out plots/exp1

For each run, produces:
  - cumulative.png     : food_in_nest over time, per source (stacked-ish)
  - rate.png           : rolling delivery rate r(t), window=50
  - t_first.png        : bar chart of t_first per source
  - heatmap_<ch>.png   : pheromone heatmap snapshots at three ticks

When multiple runs are passed in, cumulative.png and rate.png overlay
runs as separate lines.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np


def load_run(run_dir: Path) -> dict:
    header = json.loads((run_dir / "header.json").read_text(encoding="utf-8"))
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    rows = []
    with (run_dir / "events.jsonl").open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return {"dir": run_dir, "header": header, "summary": summary, "rows": rows}


def cumulative_plot(runs: list[dict], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for run in runs:
        rows = run["rows"]
        ticks = [r["tick"] for r in rows]
        sources = sorted({k for r in rows for k in r["food_in_nest_per_source"].keys()},
                         key=lambda s: int(s))
        for sid in sources:
            ys = [r["food_in_nest_per_source"].get(sid, 0) for r in rows]
            label = f"{run['dir'].name} | source {sid}"
            ax.plot(ticks, ys, label=label, alpha=0.85)
    ax.set_xlabel("tick")
    ax.set_ylabel("cumulative food in nest (per source)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def rate_plot(runs: list[dict], out: Path, window: int = 200) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    outage_spans: list[tuple[int, int]] = []
    blockade_spans: list[tuple[int, int]] = []
    for run in runs:
        rows = run["rows"]
        ticks = np.array([r["tick"] for r in rows])
        total = np.array([r["food_in_nest"] for r in rows], dtype=float)
        if len(total) < 2:
            continue
        dt = np.diff(ticks).mean() if len(ticks) > 1 else 1.0
        events_per_window = max(1, int(round(window / dt)))
        # moving rate: deliveries per tick, smoothed over `window` ticks
        delta = np.diff(total, prepend=total[0])
        kernel = np.ones(events_per_window) / events_per_window
        smoothed = np.convolve(delta, kernel, mode="same") / max(dt, 1.0)
        ax.plot(ticks, smoothed, label=run["dir"].name, alpha=0.85, linewidth=1.5)

        outages = [r["tick"] for r in rows if r.get("outage")]
        if outages:
            outage_spans.append((min(outages), max(outages)))

        # Find contiguous runs where dynamic_blocked_cells > 0 (each row is a
        # logged sample, not necessarily every tick — but the active window is
        # large compared to metrics_every so a min/max bracket is accurate).
        in_block = False
        span_start = 0
        for r in rows:
            v = r.get("dynamic_blocked_cells", 0) or 0
            if v > 0 and not in_block:
                in_block = True
                span_start = r["tick"]
            elif v == 0 and in_block:
                in_block = False
                blockade_spans.append((span_start, r["tick"]))
        if in_block:
            blockade_spans.append((span_start, rows[-1]["tick"]))

    # shade outage windows (deduped)
    outage_set = sorted(set(outage_spans))
    for span in outage_set:
        ax.axvspan(span[0], span[1], color="gray", alpha=0.15,
                   label="pheromone outage" if span == outage_set[0] else None)
    # shade dynamic-obstacle / blockade windows (deduped) in a distinct hue
    block_set = sorted(set(blockade_spans))
    for span in block_set:
        ax.axvspan(span[0], span[1], color="moccasin", alpha=0.45,
                   label="dynamic obstacle" if span == block_set[0] else None)

    ax.set_xlabel("tick")
    ax.set_ylabel(f"rolling rate r(t) (items/tick, window={window})")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def t_first_plot(runs: list[dict], out: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    labels: list[str] = []
    values: list[float] = []
    delivered: list[bool] = []
    for run in runs:
        s = run["summary"]
        for sid, t in s["t_first"].items():
            labels.append(f"{run['dir'].name}\nsource {sid}")
            if t is None:
                values.append(float("nan"))
                delivered.append(False)
            else:
                values.append(float(t))
                delivered.append(True)
    x = np.arange(len(labels))
    ax.bar(x, values, color="steelblue")
    # mark undelivered sources explicitly so they don't read as "instant"
    for i, ok in enumerate(delivered):
        if not ok:
            ax.text(i, 0, "n/a (never delivered)",
                    ha="center", va="bottom", rotation=90, fontsize=8, color="firebrick")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("t_first (tick of first delivery)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def heatmaps(run: dict, out_dir: Path, channel: str, n: int = 6) -> None:
    snap_dir = run["dir"] / "snapshots"
    snaps = sorted(snap_dir.glob("tick_*.npz"))
    if not snaps:
        return
    picks = [snaps[i] for i in np.linspace(0, len(snaps) - 1, num=min(n, len(snaps)), dtype=int)]
    static_cap = np.load(run["dir"] / "capacity.npy")
    H, W = static_cap.shape
    nests = run["header"].get("nests", [])
    foods = run["header"].get("food", [])
    stroke = [pe.withStroke(linewidth=1.6, foreground="black")]
    SUB = "₀₁₂₃₄₅₆₇₈₉"
    sub = lambda i: SUB[i] if 0 <= i < 10 else f"_{i}"

    # Lookup: snapshot tick → food_remaining_per_source. events.jsonl is sampled
    # every metrics_every ticks; we use the row at or just before the snapshot.
    rows = run["rows"]
    def remaining_at(tick: int) -> dict[str, int]:
        last: dict[str, int] = {}
        for r in rows:
            if r["tick"] > tick:
                break
            last = r.get("food_remaining_per_source", {})
        return last

    # 2 × 3 layout = 6 evenly-spaced snapshots.
    n_rows, n_cols = 2, 3
    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(4 * n_cols, 3 * n_rows + 0.8),
                             squeeze=False)
    axes_flat = axes.flatten()

    for ax_idx, ax in enumerate(axes_flat):
        if ax_idx >= len(picks):
            ax.axis("off")
            continue
        snap = picks[ax_idx]
        npz = np.load(snap)
        data = npz[channel]
        # Prefer the capacity snapshot recorded at the same tick (so dynamic
        # obstacles that were active at the snapshot tick mask the right
        # cells). Fall back to the static capacity.npy for older runs whose
        # snapshots predate this field.
        cap = npz["capacity"] if "capacity" in npz.files else static_cap
        tick = int(snap.stem.split("_")[1])
        # mask obstacles (they show as white background)
        img = np.where(cap > 0, data, np.nan)
        im = ax.imshow(img, origin="upper", cmap="viridis")
        ax.set_title(f"tick {tick}", fontsize=10)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        # Math-paper grid: thin white lines between every cell.
        ax.set_xticks(np.arange(-0.5, W, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, H, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.3, alpha=0.35)
        ax.tick_params(which="both", length=0)
        ax.set_xticks([]); ax.set_yticks([])

        # Markers — small bold letters anchored at cell centre, subscripts for
        # multi-source experiments so the label fits inside a single cell.
        for i, nest in enumerate(nests):
            label = "N" if len(nests) == 1 else f"N{sub(i)}"
            ax.text(nest["x"], nest["y"], label,
                    ha="center", va="center", fontsize=8, fontweight="bold",
                    color="white", path_effects=stroke)
        remaining = remaining_at(tick)
        for i, food in enumerate(foods):
            sid = str(food.get("id", i))
            empty = remaining.get(sid, food["amount"]) <= 0
            letter = "X" if empty else "F"
            label = letter if len(foods) == 1 else f"{letter}{sub(i)}"
            color = "lightgray" if empty else "white"
            ax.text(food["x"], food["y"], label,
                    ha="center", va="center", fontsize=8, fontweight="bold",
                    color=color, path_effects=stroke)

    fig.suptitle(f"{run['dir'].name} — pheromone:{channel}", fontsize=11)
    legend = (
        "N = nest    "
        "F (F₀, F₁, …) = food source — active    "
        "X (X₀, X₁, …) = food source — depleted    "
        "white squares = obstacles    "
        "colour intensity = pheromone level (each panel has its own scale)"
    )
    fig.text(0.5, 0.015, legend, ha="center", va="bottom",
             fontsize=8.5, color="dimgray", wrap=True)
    fig.tight_layout(rect=[0, 0.05, 1, 0.96])
    # Include the run name in the filename so multiple configs in the same
    # output folder don't overwrite each other.
    fig.savefig(out_dir / f"heatmap_{channel}__{run['dir'].name}.png", dpi=130)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="plot")
    p.add_argument("runs", nargs="+", help="one or more run directories")
    p.add_argument("--out", default="plots", help="output directory for PNGs")
    p.add_argument("--window", type=int, default=50, help="rolling-rate window (ticks)")
    args = p.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    runs = [load_run(Path(r)) for r in args.runs]

    cumulative_plot(runs, out / "cumulative.png")
    rate_plot(runs, out / "rate.png", window=args.window)
    t_first_plot(runs, out / "t_first.png")
    # One set of heatmaps (3 channels × 6 snapshots) per run. Filenames
    # carry the run name so they don't clash inside the same out folder.
    for run in runs:
        for ch in ("food", "nest", "neg"):
            heatmaps(run, out, ch, n=6)

    # also write a tiny summary.csv across runs
    csv = out / "summary.csv"
    with csv.open("w", encoding="utf-8") as f:
        f.write("run,final_tick,food_in_nest,deaths,t_first_per_source,food_per_source\n")
        for run in runs:
            s = run["summary"]
            f.write(",".join([
                run["dir"].name,
                str(s["final_tick"]),
                str(s["food_in_nest"]),
                str(s["deaths"]),
                json.dumps(s["t_first"]).replace(",", ";"),
                json.dumps(s["food_in_nest_per_source"]).replace(",", ";"),
            ]) + "\n")
    print(f"[plot] wrote PNGs + summary.csv to {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
