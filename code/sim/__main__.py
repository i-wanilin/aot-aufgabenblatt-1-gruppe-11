"""CLI entry point: python -m sim --config experiments/experiment_1.json"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .config import load_config
from .logger import JsonlLogger
from .manager import SimulationManager


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sim", description="AOT ant-colony simulator")
    p.add_argument("--config", required=True, help="path to a world configuration JSON")
    p.add_argument("--seed", type=int, default=None,
                   help="override the seed in the config (useful for replicate runs)")
    p.add_argument("--run-id", default=None,
                   help="output subdirectory name; default = config stem + seed + timestamp")
    p.add_argument("--output-dir", default=None,
                   help="override logging.output_dir from the config")
    p.add_argument("--quiet", action="store_true", help="suppress progress prints")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    if args.seed is not None:
        cfg.raw["seed"] = int(args.seed)

    log_cfg = cfg.raw.get("logging", {}) or {}
    output_dir = args.output_dir or log_cfg.get("output_dir", "runs")

    stem = Path(args.config).stem
    run_id = args.run_id or f"{stem}_seed{cfg.seed}_{time.strftime('%Y%m%d_%H%M%S')}"

    logger = JsonlLogger(
        output_dir=output_dir,
        run_id=run_id,
        metrics_every=int(log_cfg.get("metrics_every", 1)),
        snapshot_every=int(log_cfg.get("snapshot_every", 200)),
    )

    sm = SimulationManager(cfg.raw, logger)
    start = time.time()
    if not args.quiet:
        print(f"[sim] starting {run_id} (max_ticks={sm.max_ticks}, agents={len(sm.agents)})",
              file=sys.stderr)
    try:
        sm.run()
    finally:
        logger.close(sm)
    if not args.quiet:
        elapsed = time.time() - start
        print(f"[sim] done in {elapsed:.1f}s, final_tick={sm.tick}, "
              f"food_in_nest={sm.food_in_nest}, deaths={sm.deaths}",
              file=sys.stderr)
        print(f"[sim] output: {logger.dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
