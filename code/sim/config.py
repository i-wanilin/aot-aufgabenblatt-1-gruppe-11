"""Load and validate run configurations against world.schema.json."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_PATH = Path(__file__).with_name("world.schema.json")


@dataclass
class Config:
    raw: dict
    path: Path

    @property
    def seed(self) -> int:
        return int(self.raw["seed"])


class ConfigError(ValueError):
    """Raised when a config is structurally valid (per JSON-schema) but
    semantically inconsistent — e.g. a coordinate falls outside the grid."""


def _check_bounds(raw: dict) -> None:
    """Post-validate the config: coordinates must lie inside the grid, and
    nest / food ids must be unique. JSON-schema can express neither (the
    grid size is itself a config value, and uniqueItems doesn't reach into
    a single property of array items). Raising here gives a clear error
    instead of a later IndexError inside numpy or silently merged metrics.
    """
    w = int(raw["grid"]["width"])
    h = int(raw["grid"]["height"])

    def _in(x: int, y: int) -> bool:
        return 0 <= x < w and 0 <= y < h

    def _check_unique_ids(items: list, kind: str) -> None:
        seen: set[int] = set()
        for i, it in enumerate(items):
            if "id" not in it:
                continue
            iid = int(it["id"])
            if iid in seen:
                raise ConfigError(f"{kind}[{i}].id={iid} is duplicated; ids must be unique")
            seen.add(iid)

    _check_unique_ids(raw.get("nests", []), "nests")
    _check_unique_ids(raw.get("food", []), "food")

    for i, n in enumerate(raw.get("nests", [])):
        if not _in(int(n["x"]), int(n["y"])):
            raise ConfigError(f"nests[{i}] at ({n['x']}, {n['y']}) is outside grid {w}x{h}")
    for i, f in enumerate(raw.get("food", [])):
        if not _in(int(f["x"]), int(f["y"])):
            raise ConfigError(f"food[{i}] at ({f['x']}, {f['y']}) is outside grid {w}x{h}")
    for i, ob in enumerate(raw.get("obstacles", [])):
        x0, y0 = int(ob["x"]), int(ob["y"])
        ow = int(ob.get("w", 1)); oh = int(ob.get("h", 1))
        if not _in(x0, y0) or x0 + ow > w or y0 + oh > h:
            raise ConfigError(
                f"obstacles[{i}] rect ({x0},{y0},w={ow},h={oh}) is outside grid {w}x{h}"
            )
    for i, ob in enumerate(raw.get("dynamic_obstacles", [])):
        x0, y0 = int(ob["x"]), int(ob["y"])
        ow = int(ob.get("w", 1)); oh = int(ob.get("h", 1))
        if not _in(x0, y0) or x0 + ow > w or y0 + oh > h:
            raise ConfigError(
                f"dynamic_obstacles[{i}] rect ({x0},{y0},w={ow},h={oh}) is outside grid {w}x{h}"
            )
        if int(ob["appears_at"]) >= int(ob["disappears_at"]):
            raise ConfigError(
                f"dynamic_obstacles[{i}]: appears_at ({ob['appears_at']}) must be < "
                f"disappears_at ({ob['disappears_at']})"
            )
    ws = raw.get("warm_start", {})
    for i, t in enumerate(ws.get("trails", [])):
        if not _in(int(t["x"]), int(t["y"])):
            raise ConfigError(f"warm_start.trails[{i}] at ({t['x']}, {t['y']}) is outside grid {w}x{h}")
    for i, ln in enumerate(ws.get("lines", [])):
        sx, sy = int(ln["start"][0]), int(ln["start"][1])
        ex, ey = int(ln["end"][0]), int(ln["end"][1])
        if not _in(sx, sy) or not _in(ex, ey):
            raise ConfigError(
                f"warm_start.lines[{i}] from ({sx},{sy}) to ({ex},{ey}) outside grid {w}x{h}"
            )


def load_config(path: str | Path) -> Config:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=raw, schema=schema)
    _check_bounds(raw)
    return Config(raw=raw, path=p.resolve())
