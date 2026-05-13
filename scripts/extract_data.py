#!/usr/bin/env python3
"""
One-shot extraction script for PRD-002 Phase 1.

Reads hardcoded dicts from weather/ source modules and writes them as JSON
files under weather/data/. Run once during Phase 1, then delete.

Usage:
    python scripts/extract_data.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "weather" / "data"


def _enum_to_str(value: Any) -> Any:
    """Convert WeatherCondition enum values to their string form."""
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(k): _enum_to_str(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_enum_to_str(v) for v in value]
    return value


def _write(path: Path, data: Any, *, sort: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=sort)
        f.write("\n")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    # Task 1.1 — models.py: LOCATION_ALIASES, WeatherCondition, CONDITION_EMOJI
    from weather.models import LOCATION_ALIASES, CONDITION_EMOJI, WeatherCondition

    _write(DATA / "location-aliases.json", LOCATION_ALIASES)
    _write(DATA / "weather-conditions.json", [c.value for c in WeatherCondition])
    _write(
        DATA / "condition-emoji.json",
        {c.value: emoji for c, emoji in CONDITION_EMOJI.items()},
    )

    # Task 1.2 — HKO
    from weather.providers.hko import HKO_ICON_MAP

    _write(DATA / "condition-maps" / "hko-icons.json", _enum_to_str(HKO_ICON_MAP))

    # Task 1.3 — JMA
    from weather.providers.jma import JMA_AREA_CODES, JMA_WEATHER_CODE_MAP

    _write(DATA / "cities" / "jma-area-codes.json", JMA_AREA_CODES)
    _write(
        DATA / "condition-maps" / "jma-codes.json",
        _enum_to_str(JMA_WEATHER_CODE_MAP),
    )

    # Task 1.4 — US NWS
    from weather.providers.us_nws import US_CITIES, NWS_CONDITION_MAP

    # Tuples become arrays in JSON
    _write(
        DATA / "cities" / "us-nws.json",
        {k: list(v) for k, v in US_CITIES.items()},
    )
    _write(
        DATA / "condition-maps" / "nws-conditions.json",
        _enum_to_str(NWS_CONDITION_MAP),
    )

    # Task 1.5 — SG NEA
    from weather.providers.sg_nea import SG_CONDITION_MAP

    _write(
        DATA / "condition-maps" / "sg-nea-forecast.json",
        _enum_to_str(SG_CONDITION_MAP),
    )

    # Task 1.6 — DWD
    from weather.providers.de_dwd import DE_CITIES, BRIGHTSKY_CONDITION_MAP

    _write(
        DATA / "cities" / "de-dwd.json",
        {k: list(v) for k, v in DE_CITIES.items()},
    )
    _write(
        DATA / "condition-maps" / "brightsky-conditions.json",
        _enum_to_str(BRIGHTSKY_CONDITION_MAP),
    )

    # Task 1.7 — OpenWeatherMap (int keys → string keys for JSON)
    from weather.providers.openweathermap import OpenWeatherMapProvider

    owm_map = {str(k): v.value for k, v in OpenWeatherMapProvider.CONDITION_MAP.items()}
    _write(DATA / "condition-maps" / "owm-codes.json", owm_map)

    # Task 1.8 — batch-2: CWA, Met Office, BOM, MetService
    _extract_batch2()

    # Task 1.9 — batch-2: BMKG, KMA, TMD
    _extract_batch2_remainder()


def _extract_batch2() -> None:
    """Extract condition maps + cities from CWA, Met Office, BOM, MetService."""
    import importlib

    targets = [
        ("tw_cwa", "cwa"),
        ("uk_metoffice", "metoffice"),
        ("au_bom", "bom"),
        ("nz_metservice", "metservice"),
    ]
    for module_name, slug in targets:
        mod = importlib.import_module(f"weather.providers.{module_name}")
        _extract_module_dicts(mod, slug)


def _extract_batch2_remainder() -> None:
    """Extract condition maps + cities from BMKG, KMA, TMD."""
    import importlib

    targets = [
        ("id_bmkg", "bmkg"),
        ("kr_kma", "kma"),
        ("th_tmd", "tmd"),
    ]
    for module_name, slug in targets:
        mod = importlib.import_module(f"weather.providers.{module_name}")
        _extract_module_dicts(mod, slug)


def _extract_module_dicts(mod: Any, slug: str) -> None:
    """
    Extract any module-level dict whose values are WeatherCondition (→ condition map)
    or whose values are tuples of 2 floats (→ city coords).
    """
    from weather.models import WeatherCondition

    condition_map: dict[str, str] = {}
    cities: dict[str, list[float]] = {}

    for name, val in vars(mod).items():
        if name.startswith("_") or not isinstance(val, dict) or not val:
            continue
        first_value = next(iter(val.values()))

        if isinstance(first_value, WeatherCondition):
            # Condition map
            for k, v in val.items():
                condition_map[str(k)] = v.value
        elif (
            isinstance(first_value, tuple)
            and len(first_value) == 2
            and all(isinstance(x, (int, float)) for x in first_value)
        ):
            # City coordinates
            for k, v in val.items():
                cities[str(k)] = list(v)

    if condition_map:
        _write(DATA / "condition-maps" / f"{slug}-conditions.json", condition_map)
    if cities:
        _write(DATA / "cities" / f"{slug}.json", cities)


if __name__ == "__main__":
    main()
