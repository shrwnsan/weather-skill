# Eval-001: PRD-002 Phase 0 + Phase 1 + Phase 2 Review

**Reviewed commits:**
- `67a78b6` — docs(prd-002): finalize PRD with Phase-0 decisions and add tasks file
- `fd1d52c` — feat(prd-002 phase 1): extract shared data layer to weather/data/
- `807e1fb` — feat(prd-002 phase 2): Bun/TypeScript scaffold + core types

**Date:** 2026-05-13
**Status:** Open

---

## Commit 67a78b6 (Docs)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| D-1 | Medium | Effort estimate contradiction — scope table says v0.1 ETA "~15h" but detailed estimate mid-points ~25h. Commit message says "re-baseline to ~25h" but scope table wasn't updated. | Open |
| D-2 | Medium | Directory naming inconsistency within the PRD — repo structure tree (L88) says `condition-maps/` (hyphen) but `importlib.resources` code example (L212) references `weather.data.condition_maps` (underscore). | Open |
| D-3 | Medium | Repository structure (L125-138) lists all 13 Bun providers without marking the 8 batch-2 providers as deferred. Contradicts scope section. | Open |
| D-4 | Low | Missing Phase 4 note in dependency graph — jumps from Phase 3 to Phase 5 with no comment. | Open |
| D-5 | Low | Task 1.9 assumes a single `kma-conditions.json` but the actual provider has two maps (PTY + sky). Task spec didn't anticipate the split. | Open |

## Commit fd1d52c (Phase 1 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| I-1 | Medium | `scripts/extract_data.py` and `scripts/refactor_providers.py` reference `condition-maps/` (hyphen) but the actual directory is `condition_maps/` (underscore). Scripts are explicitly kept for PRD-002b re-extraction and will fail if re-run. | Open |
| I-2 | Medium | Float trailing zeros lost in city coordinate JSON — e.g. `(-74.0060, -112.0740)` becomes `[-74.006, -112.074]`. No runtime impact but canonical data loses precision signaling. Affects `us-nws.json` and `metoffice.json`. | Open |
| I-3 | Low | CI wheel smoke test threshold is `>= 18` but 21 JSON files exist. Up to 3 files could disappear without CI catching it. Should be `>= 21`. File: `.github/workflows/python-ci.yml:44`. | Open |
| I-4 | Low | `weather/data/cities/metoffice.json` was extracted but `uk_metoffice.py` still hardcodes `UK_CITIES`. Dead data file in Python — either load it or remove it. **Bun side resolved**: Phase 2 imports it as `METOFFICE_CITIES` in `src/data-loader.ts`. | Partial |
| I-5 | Low | `weather/data/weather-conditions.json` exists but no Python code loads it at runtime. **Bun side resolved**: Phase 2 imports it to build `VALID_CONDITION_VALUES` for `toCondition()` in `src/data-loader.ts`. | Partial |
| I-6 | Low | `cli.py:137` uses duck-typing (`hasattr(o, "value") and hasattr(type(o), "__members__")`) instead of `isinstance(o, enum.Enum)` for enum serialization. Works but fragile. | Open |
| I-7 | Low | `models.py:36` — `from .data.loader import load_json` appears mid-file (after enum def). Works (avoids circular dependency) but deserves a comment explaining why. | Open |

## Commit 807e1fb (Phase 2 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P2-1 | High | `makeWeatherData` in `src/models.ts` does not set `condition_raw: ""` default. Python's dataclass always has `condition_raw` (defaults to `""`). Missing default means Bun providers that don't explicitly set it will omit the key from JSON output, breaking cross-runtime parity tests. | Fixed |
| P2-2 | High | `condition_raw` is optional (`string?`) in `src/types.ts:74` but required with default `""` in Python's `weather/models.py:70`. `JSON.stringify` omits `undefined` values, so the serialized JSON diverges from Python's `dataclasses.asdict()` which always includes `condition_raw: ""`. | Fixed |
| P2-3 | Medium | `tsconfig.json` uses `"types": ["bun"]` (resolves to `@types/bun`) but task 2.1 spec says `"types": ["bun-types"]`. The newer `"bun"` convention is correct for Bun 1.1.30+ — update the task spec to match. | Open |
| P2-4 | Medium | `Math.round` in `src/models.ts` (tempRangeStr, windStr) uses "round half up" while Python's `:.0f` uses banker's rounding (round half to even). E.g. `Math.round(0.5)` = 1 vs Python `f"{0.5:.0f}"` = "0". Negligible for weather data but could cause edge-case snapshot test failures. | Open |
| P2-5 | Low | `bunfig.toml` references `./test/setup.ts` which doesn't exist yet (Phase 7). Comment explains the situation but a TODO link to task 7.3 would improve traceability. | Open |

**Verified correct in Phase 2:**
- All 21 JSON files imported in `src/data-loader.ts` (3 top-level + 4 city + 14 condition maps)
- `buildConditionMap` correctly drops KMA null sentinel (`"0": null`)
- Type casts for city coordinates (`as unknown as Record<string, [number, number]>`) are safe
- `toCondition` returns `Unknown` for null/undefined/invalid values
- AQHI and AQI threshold tables match Python exactly
- `effectiveFeelsLike` matches Python logic (feels_like → calculate → temperature fallback)
- `normalizeLocation` / `parseLocation` match Python behavior
- `calculateFeelsLike` uses same NWS/NOAA simplified formulas with correct m/s input
- `.gitignore` `/weather` + `!/weather/` pattern correctly ignores compiled binary while tracking Python package

---

## Quick Wins

These are low-effort fixes that improve correctness:

1. Update both scripts to use `condition_maps` (underscore) — blocks PRD-002b re-extraction (I-1)
2. Bump CI threshold from `>= 18` to `>= 21` (I-3)
3. Either wire `metoffice.json` into `uk_metoffice.py` or remove the file (I-4 Python side)
4. Update PRD scope table ETA from "~15h" to "~25h" (D-1)
5. Add `condition_raw: ""` to `makeWeatherData` defaults in `src/models.ts` (P2-1) ✅
6. Update task 2.1 spec to reflect `"types": ["bun"]` instead of `"bun-types"` (P2-3)
