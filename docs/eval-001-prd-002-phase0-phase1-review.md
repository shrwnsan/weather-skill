# Eval-001: PRD-002 Phase 0 + Phase 1 + Phase 2 + Phase 3 Review

**Reviewed commits:**
- `67a78b6` — docs(prd-002): finalize PRD with Phase-0 decisions and add tasks file
- `fd1d52c` — feat(prd-002 phase 1): extract shared data layer to weather/data/
- `807e1fb` — feat(prd-002 phase 2): Bun/TypeScript scaffold + core types
- `1eba637` — feat(prd-002 phase 3): port batch-1 providers + OWM to Bun

**Date:** 2026-05-13 (updated 2026-05-15)
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

## Commit 1eba637 (Phase 3 Implementation)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P3-1 | **High** | `parseLocation` in `src/models.ts` does not apply `normalizeLocation` / `LOCATION_ALIASES`. Python's `WeatherSkill.parse_location()` resolves aliases (e.g. "hk" -> "hong kong", "nyc" -> "new york") before passing to providers. The TS version just does `raw.toLowerCase().trim()`, so alias-based queries fail in Bun. Affects every provider. | ✅ Fixed |
| P3-2 | **High** | `hko.ts` declares `supportsAirQuality = true` but never populates the `aqhi` field from the HKO API response. Python has the same declaration gap, so this is parity-preserving — but the flag misleads downstream consumers. | Deferred (parity-preserving — needs cross-runtime fix) |
| P3-3 | Medium | `us_nws.ts:263-266` — forecast date deduplication uses `toISOString().slice(0,10)` which converts to UTC. For US western time zones near midnight, a period like `2026-05-13T23:00:00-04:00` becomes `2026-05-14` in UTC, misassigning the forecast day. Python uses `.date()` which preserves the local date from the ISO offset. | ✅ Fixed |
| P3-4 | Medium | `openweathermap.ts` stores `wind_speed` as m/s (raw OWM value) to match Python parity, but `WeatherData.wind_speed` is documented as `// km/h` in both `types.ts:66` and `models.py:61`. The `windStr()` helper formats with "km/h" units, producing incorrect output for OWM-sourced data. | Deferred (intentional Python parity quirk — coordinate fix in PRD-002b or follow-up Python PR) |
| P3-5 | Medium | `jma.ts:53` — `supportsLocation` only checks `JMA_AREA_CODES` keys. Python includes Japanese locale names ("日本", "東京", etc.) via an explicit set union. If `jma-area-codes.json` lacks Japanese keys, Japanese-language queries will fail in Bun. | ✅ Fixed |
| P3-6 | Low | `hko.ts:157-163` — `observedAt` constructed as UTC (`Date.UTC(...)`) while Python parses `BulletinTime` as a naive datetime (implicitly HKT, UTC+8). Results in 8-hour offset. | Deferred to Phase 7 (cross-runtime TZ normalization) |
| P3-7 | Low | `jma.ts:79` — `getForecast` defaults to `days=3` while Python defaults to `days=7`. JMA API supports 7-day forecasts. | ✅ Fixed |
| P3-8 | Low | `sg_nea.ts:239-245` — `forecast_date` parsed via `new Date(dateStr)` (UTC midnight) vs Python's `datetime.strptime(date_str, "%Y-%m-%d").date()` (naive date). Minor timezone ambiguity. | Deferred to Phase 7 (cross-runtime date-vs-datetime normalization) |
| P3-9 | Low | `skill.ts:176-191` — `formatSimple` fallback omits humidity, wind, and emoji compared to Python's `_format_simple`. Simplified but less informative when no formatter is registered. | ✅ Fixed |

**Verified correct in Phase 3:**
- All providers set `condition_raw` to a string (defaults to `""` when unavailable) — P2-1/P2-2 fix confirmed in practice
- All providers use conditional-spread pattern for optional fields (`...(v != null ? { f: v } : {})`)
- All providers re-throw `LocationNotSupportedError` and wrap other errors with `ProviderError`
- HKO icon mapping, PSR rain probability, HTML stripping match Python
- JMA dual-endpoint parallel fetch via `Promise.all`, 3-level timeSeries traversal
- SG NEA partial-failure-tolerant parallel fetch via `fetchJsonSafe`, PSI extraction
- NWS User-Agent header (`WeatherSkill/1.0 (support@weather-skill.io)`) — avoids 403
- NWS `degToDirection` correctly handles negative degrees with `(index + 16) % 16`
- NWS F->C, m/s->km/h, Pa->hPa, m->km conversions all match Python
- OWM `q=` query, `units=metric`, forecast aggregation via `mostCommon`, AQI 1-5 scale
- Bootstrap registers HKO/SGNEA/JMA/NWS unconditionally, OWM conditionally on API key
- Priority sorting handled by `WeatherSkill` constructor

---

## Quick Wins

These are low-effort fixes that improve correctness:

1. Update both scripts to use `condition_maps` (underscore) — blocks PRD-002b re-extraction (I-1)
2. Bump CI threshold from `>= 18` to `>= 21` (I-3)
3. Either wire `metoffice.json` into `uk_metoffice.py` or remove the file (I-4 Python side)
4. Update PRD scope table ETA from "~15h" to "~25h" (D-1)
5. Add `condition_raw: ""` to `makeWeatherData` defaults in `src/models.ts` (P2-1) ✅
6. Update task 2.1 spec to reflect `"types": ["bun"]` instead of `"bun-types"` (P2-3)
7. **Fix `parseLocation` to apply `normalizeLocation`** — one-line fix in `src/models.ts`, unblocks all alias-based queries in Bun (P3-1) ✅
8. Fix JMA `getForecast` default from `days=3` to `days=7` (P3-7) ✅
