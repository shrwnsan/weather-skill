"""
Cross-runtime JSON parity gate (PRD-002 Phase 7.7) — Python side.

For each supported (provider, mode) pair, this suite:
    1. Builds a `WeatherSkill` from the default factory.
    2. Fetches data against the `mock_http` fixture + `frozen_clock`
       at 2026-01-01T00:00:00+00:00.
    3. Serializes the result with `weather.cli.to_jsonable` +
       `json.dumps(..., sort_keys=True, ensure_ascii=False, indent=2)`
       — the same code path as the `--format json` CLI flag.
    4. Compares the bytes to `fixtures/parity/<key>.json`.

The matching Bun suite (`test/parity.test.ts`) asserts against the
same snapshot files using `src/cli.ts:toJson`. If both sides pass
against the same snapshot, byte-for-byte parity is proven
transitively.

Refresh snapshots with:
    UPDATE_PARITY_SNAPSHOTS=1 pytest tests/test_parity.py
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from weather.bootstrap import build_default_skill
from weather.cli import to_jsonable

SNAPSHOTS_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "parity"
_UPDATE = os.environ.get("UPDATE_PARITY_SNAPSHOTS") == "1"


# (key, location, provider, mode, days). `days` is ignored for `current`.
# JMA forecast intentionally OUT of the parity matrix: Bun's provider
# preserves the raw timeDefines instant (JST midnight = 15:00Z prior
# day), while Python's provider calls `.date()` first. Tracked alongside
# P7.4-5 in the JMA cross-runtime follow-up.
# SG NEA + OpenWeather also out (P7.4-4 crash; OWM `needs_capture`).
_CASES: list[tuple[str, str, str, str, int]] = [
    ("hko-current",       "Hong Kong", "hko", "current",  0),
    ("hko-forecast-3",    "Hong Kong", "hko", "forecast", 3),
    ("jma-current",       "Tokyo",     "jma", "current",  0),
    ("us_nws-current",    "New York",  "nws", "current",  0),
    ("us_nws-forecast-5", "New York",  "nws", "forecast", 5),
]


def _serialize(payload: Any) -> str:
    """Emit the canonical wire-format JSON string (with trailing newline)."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


@pytest.mark.parametrize(
    ("key", "location", "provider", "mode", "days"),
    _CASES,
    ids=[c[0] for c in _CASES],
)
def test_parity(
    mock_http,
    frozen_clock,
    key: str,
    location: str,
    provider: str,
    mode: str,
    days: int,
) -> None:
    skill = build_default_skill()

    async def _go() -> Any:
        if mode == "current":
            data = await skill.get_current(location, provider)
            return to_jsonable(asdict(data))
        days_data = await skill.get_forecast(location, days, provider)
        return [to_jsonable(asdict(d)) for d in days_data]

    output = asyncio.run(_go())
    actual = _serialize(output)
    snapshot_path = SNAPSHOTS_ROOT / f"{key}.json"

    if _UPDATE or not snapshot_path.exists():
        snapshot_path.write_text(actual, encoding="utf-8")
        return

    expected = snapshot_path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Parity snapshot mismatch for {key}.\n"
        f"Expected (from fixtures/parity/{key}.json):\n{expected}\n"
        f"Actual (from Python skill):\n{actual}"
    )
