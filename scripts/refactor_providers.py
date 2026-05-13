#!/usr/bin/env python3
"""
Replace hardcoded module-level dicts in provider files with load_json calls.

Run once during PRD-002 Phase 1 task 1.10. Idempotent: skips files where
the dict has already been replaced.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (file path, [(dict_var_name, json_path_parts, value_kind), ...])
# value_kind:
#   "condition" → values are WeatherCondition enums (need rebuild via WeatherCondition(v))
#   "city"      → values are tuples of floats (need rebuild via tuple())
#   "raw"       → load directly, no rebuild
TARGETS = [
    # Batch 1 + OWM (mandatory for v0.1 Bun port)
    ("weather/providers/us_nws.py", [
        ("US_CITIES", ("cities", "us-nws.json"), "city"),
        ("NWS_CONDITION_MAP", ("condition-maps", "nws-conditions.json"), "condition"),
    ]),
    ("weather/providers/sg_nea.py", [
        ("SG_CONDITION_MAP", ("condition-maps", "sg-nea-forecast.json"), "condition"),
    ]),
    ("weather/providers/de_dwd.py", [
        ("DE_CITIES", ("cities", "de-dwd.json"), "city"),
        ("BRIGHTSKY_CONDITION_MAP", ("condition-maps", "brightsky-conditions.json"), "condition"),
    ]),
    # Batch 2 (de-risks PRD-002b — condition maps only; complex city/station dicts stay
    # hardcoded for now and will be addressed in PRD-002b)
    ("weather/providers/tw_cwa.py", [
        ("CWA_CONDITION_MAP", ("condition-maps", "cwa-conditions.json"), "condition"),
    ]),
    ("weather/providers/uk_metoffice.py", [
        ("METOFFICE_WEATHER_CODES", ("condition-maps", "metoffice-conditions.json"), "condition_int"),
    ]),
    ("weather/providers/au_bom.py", [
        ("BOM_CONDITION_MAP", ("condition-maps", "bom-conditions.json"), "condition"),
    ]),
    ("weather/providers/nz_metservice.py", [
        ("NZ_CONDITION_MAP", ("condition-maps", "metservice-conditions.json"), "condition"),
    ]),
    ("weather/providers/id_bmkg.py", [
        ("BMKG_CONDITION_MAP", ("condition-maps", "bmkg-conditions.json"), "condition"),
    ]),
    ("weather/providers/kr_kma.py", [
        ("KMA_PTY_MAP", ("condition-maps", "kma-pty.json"), "condition_optional"),
        ("KMA_SKY_MAP", ("condition-maps", "kma-sky.json"), "condition"),
    ]),
    ("weather/providers/th_tmd.py", [
        ("TMD_CONDITION_MAP", ("condition-maps", "tmd-conditions.json"), "condition"),
    ]),
]


def _find_dict_block(lines: list[str], var_name: str) -> tuple[int, int] | None:
    """Find (start_idx, end_idx) of `var_name = {` ... `}` block. 0-indexed inclusive."""
    pattern = re.compile(rf"^\s*{re.escape(var_name)}\s*=\s*\{{")
    for i, line in enumerate(lines):
        if pattern.match(line):
            depth = line.count("{") - line.count("}")
            if depth == 0:
                return (i, i)
            for j in range(i + 1, len(lines)):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0:
                    return (i, j)
            return None
    return None


def _make_replacement(var_name: str, json_parts: tuple[str, ...], kind: str) -> list[str]:
    parts_str = ", ".join(f'"{p}"' for p in json_parts)
    if kind == "raw":
        return [
            f"# {var_name} (loaded from weather/data/{'/'.join(json_parts)})\n",
            f"{var_name} = load_json({parts_str})\n",
        ]
    if kind == "condition":
        return [
            f"# {var_name} (loaded from weather/data/{'/'.join(json_parts)})\n",
            f"{var_name} = {{\n",
            f"    k: WeatherCondition(v)\n",
            f"    for k, v in load_json({parts_str}).items()\n",
            "}\n",
        ]
    if kind == "condition_int":
        # Original Python used int keys; JSON forces string keys → convert back
        return [
            f"# {var_name} (loaded from weather/data/{'/'.join(json_parts)})\n",
            f"{var_name} = {{\n",
            f"    int(k): WeatherCondition(v)\n",
            f"    for k, v in load_json({parts_str}).items()\n",
            "}\n",
        ]
    if kind == "condition_optional":
        return [
            f"# {var_name} (loaded from weather/data/{'/'.join(json_parts)})\n",
            f"{var_name} = {{\n",
            f"    k: (WeatherCondition(v) if v is not None else None)\n",
            f"    for k, v in load_json({parts_str}).items()\n",
            "}\n",
        ]
    if kind == "city":
        return [
            f"# {var_name} (loaded from weather/data/{'/'.join(json_parts)})\n",
            f"{var_name} = {{\n",
            f"    k: tuple(v)\n",
            f"    for k, v in load_json({parts_str}).items()\n",
            "}\n",
        ]
    raise ValueError(f"unknown kind: {kind}")


def _ensure_loader_import(lines: list[str]) -> list[str]:
    """Add 'from ..data.loader import load_json' if not already present."""
    if any("from ..data.loader import load_json" in line for line in lines):
        return lines
    # Insert right after `from ..models import ...`
    for i, line in enumerate(lines):
        if line.startswith("from ..models import"):
            return lines[: i + 1] + ["from ..data.loader import load_json\n"] + lines[i + 1 :]
    raise RuntimeError("couldn't find `from ..models import` line to anchor loader import")


def process(file_path: pathlib.Path, replacements: list[tuple[str, tuple[str, ...], str]]) -> bool:
    if not file_path.exists():
        print(f"SKIP (missing): {file_path}")
        return False
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False

    # Bottom-up replacement to preserve indices
    for var_name, json_parts, kind in reversed(replacements):
        block = _find_dict_block(lines, var_name)
        if block is None:
            print(f"SKIP {file_path.name}::{var_name} (already refactored or not found)")
            continue
        start, end = block
        # Strip a preceding "# <var_name> ..." comment line if present (avoid duplicate)
        if start > 0 and lines[start - 1].strip().startswith("#"):
            start -= 1
        replacement = _make_replacement(var_name, json_parts, kind)
        lines = lines[:start] + replacement + lines[end + 1 :]
        changed = True
        print(f"REPLACED {file_path.name}::{var_name}")

    if changed:
        lines = _ensure_loader_import(lines)
        file_path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    any_changed = False
    for rel_path, repls in TARGETS:
        if process(ROOT / rel_path, repls):
            any_changed = True
    return 0 if any_changed else 1


if __name__ == "__main__":
    sys.exit(main())
