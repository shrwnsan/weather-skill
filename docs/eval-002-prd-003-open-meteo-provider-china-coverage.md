# Eval-002: PRD-003 + Tasks-003 Review — Open-Meteo Provider + China City Coverage

**Reviewed commit:**
- `122c7b1` — docs: add PRD-003 and tasks for Open-Meteo provider + China city coverage

**Date:** 2026-05-29
**Status:** Open (pre-implementation)

---

## PRD-003 Document Review

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P-1 | **Critical** | Non-Goals states *"Python-runtime port… a separate task"* but Tasks-003 includes full Tier 1B (Python chain: tasks 3.1, 3.2) and Tier 2 task 4.2 (Python tests). The PRD and tasks contradict each other — one must be updated. | Open |
| P-2 | Medium | Provider priority table lists BMKG at priority 9. Actual code: `weather/providers/id_bmkg.py:85` sets `priority = 8` (same as DWD). The table should show BMKG at priority 8. | Open |
| P-3 | Medium | Bun `parseCurrent` sketch never sets `observed_at`. Open-Meteo returns `current.time` (ISO timestamp) — this should be parsed and included. The frozen-time test setup would mask the issue (undefined vs Date), but production `WeatherData` would have `observed_at: undefined`. | Open |
| P-4 | Low | Wind speed unit inconsistency not acknowledged. Open-Meteo returns `wind_speed_10m` in km/h. OWM stores m/s (documented quirk in `openweathermap.ts`). The `WeatherData.wind_speed` field is documented as km/h in both runtimes. Open-Meteo will store km/h directly while OWM stores m/s — 3.6× visible discrepancy between providers for the same field. Not introduced by this PRD but should be flagged as a known cross-provider inconsistency. | Open |
| P-5 | Low | Non-Goals mentions *"needs_capture: true"* for parity testing deferral, but Task 1.4 sets `needs_capture: false` (correct for a hand-crafted fixture). Update the PRD non-goal to match. | Open |
| P-6 | Low | WMO code 66 (`"66": "rain"`) maps "Light freezing rain" to `rain` rather than `sleet`. Defensible, but a brief comment in `wmo-codes.json` would document the mapping choice. | Open |

**Verified correct in PRD-003:**
- Problem statement accurately describes the gap: no Open-Meteo provider, no Chinese city coordinates
- Provider chain analysis (priority 10 OWM → gap) is correct
- Open-Meteo vs OWM comparison table is accurate (key required vs zero-config, coverage models, field richness)
- API endpoint, parameters, and response shape match the real Open-Meteo v1/forecast API
- WMO 4680 code mapping covers all 28 common weather codes (verified against WMO spec)
- `supportsLocation` design (direct coords → CN_CITIES → US_NWS_CITIES → DE_DWD_CITIES → METOFFICE_CITIES) is correct and matches the city data files present in the repo
- `titleCase` function handles apostrophe-containing names correctly — `"xi'an"` alias resolves to `"Xian"` via alias lookup before reaching `titleCase`, so the apostrophe never hits the split logic
- Chinese city coordinate data (10 cities + country key) has correct lat/lon values (spot-checked Shenzhen, Beijing, Shanghai)
- Collision analysis for aliases (`sh`, `cn`, `bj`, `gz`, `sz`) is thorough — all verified absent from existing `location-aliases.json` (276 entries, keys sorted, last 5 are Korean/Japanese — no conflicts)
- New/modified file lists are complete and accurate against actual repo structure
- Implementation plan phases are correctly ordered (data → loader → provider → integration → tests → docs)
- Success criteria cover the key scenarios: Chinese city direct query, alias query, non-interference with existing providers (JMA, NWS), no OWM key required
- Provider count 13 → 14 is correct (13 existing providers verified)

---

## Tasks-003 Document Review

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| T-1 | **Critical** | Task 1.4 manifest format uses `{ "responses": [{ "url": "...", "file": "..." }] }` but both `test/setup.ts` and `tests/conftest.py` expect `{ "urls": { "https://...": "filename.json" } }`. The `loadFixtures()` / `_load_manifests()` functions iterate `Object.entries(manifest.urls)` — the proposed `responses` array will never be read. Every `mockFetch`/`mock_http` call for Open-Meteo will 404, breaking both Bun and Python test suites. | Open |
| T-2 | **Critical** | No task updates `test/setup.ts` PROVIDERS array to include `"open_meteo"`. The fixture preloader at line 16 has a hardcoded `PROVIDERS` list — without `"open_meteo"`, `loadFixtures()` skips the entire `fixtures/api-responses/open_meteo/` directory. Must be added as part of Task 1.4 or a new task. | Open |
| T-3 | **Critical** | No task updates `tests/conftest.py` `_PROVIDERS` tuple to include `"open_meteo"`. The Python `mock_http` fixture only loads manifests for the 5 listed providers. Without `"open_meteo"`, the Python `mock_http` fixture will not serve Open-Meteo fixtures, breaking all Python tests in Task 4.2. Must be added as part of Task 1.4 or a new task. | Open |
| T-4 | Medium | Task 3.1 Python implementation loads WMO code map as `int(k)` keys. The `wmo-codes.json` file has string keys (JSON requirement). Python `int("0")` works, but the `WeatherCondition(v)` call uses the string value from the map. The `buildConditionMap` pattern used by the Bun data-loader validates values against `VALID_CONDITION_VALUES` — the Python side has no such validation. If a typo in `wmo-codes.json` maps to an invalid condition (e.g. `"sunnyy"`), the Python `WeatherCondition("sunnyy")` will raise `ValueError` at module load time with no graceful fallback. Low risk but worth noting. | Open |
| T-5 | Low | Task 3.2 does not mention updating `weather/providers/__init__.py`, which has a docstring listing all providers with their priority and coverage. The list should be updated to include Open-Meteo. | Open |
| T-6 | Low | Dependency graph says Tier 2 tests "wait for Tier 1 + 1.4" but the graph visual shows no arrow from 1.4 to Tier 2. Minor doc inconsistency — the textual description is authoritative and correct. | Open |

**Verified correct in Tasks-003:**
- Dependency graph is well-structured and accurate (4 parallel agents, 5 tiers)
- Tier 0 tasks are correctly marked as fully parallel (4 independent file changes)
- Tier 1A Bun chain (2.1 → 2.2 → 2.3) has correct sequential dependencies
- Tier 1B Python chain (3.1 → 3.2) has correct sequential dependencies
- Tier 1A and 1B are correctly marked parallel with each other
- Task 1.1 (`wmo-codes.json`): 28 codes, correct mappings, verification script is correct
- Task 1.2 (`cn.json`): 11 entries (10 cities + `"china"` country key), correct format, verification script is correct
- Task 1.3 (`location-aliases.json`): 29 new aliases, correct placement after existing entries, conflict check is accurate
- Task 1.4: fixture response shape matches real Open-Meteo API output (verified field names, types, nesting)
- Task 2.1: import placement in `src/data-loader.ts` is correct (after existing city imports, after `tmdConditionsRaw`), export naming matches existing patterns (`CN_CITIES`, `WMO_CODE_MAP`)
- Task 2.2: provider sketch follows established patterns from `openweathermap.ts` (error handling, `makeWeatherData` usage, conditional spread for optional fields)
- Task 2.2: `resolveCoords` merge order (CN → US → DE → MetOffice) is sensible and prevents shadowing
- Task 2.2: `fetchJson` error handling mirrors `openweathermap.ts` pattern (catch fetch errors → `ProviderError`, HTTP status check)
- Task 2.2: `parseForecast` correctly maps `daily.time[i]` arrays to `WeatherData` with `forecast_date`
- Task 2.3: bootstrap placement (after CWA key-gated block) is correct — Open-Meteo is unconditional and last
- Task 2.3: index.ts export placement follows alphabetical-adjacent pattern
- Task 3.1: Python provider follows `de_dwd.py` async patterns (`run_in_executor`, `urllib.request`) — correct for sync HTTP in async context
- Task 3.1: Python `_resolve_coords` uses `or` short-circuit (same as DWD pattern) — correct
- Task 3.2: Python bootstrap placement (after OWM block) is correct
- Task 4.1: Bun test structure follows `hko.test.ts` / `us_nws.test.ts` patterns (describe blocks, `parseLocation`, `mockFetch`)
- Task 4.1: test cases cover the key scenarios (supportsLocation for CN/US/DE/unknown, getCurrent parsing, alias resolution)
- Task 4.2: Python test structure follows existing pytest patterns (conftest `mock_http` fixture usage)
- Task 5.1: CHANGELOG entries are thorough and accurate
- Task 5.2: PRD status update from Draft → Complete is standard practice
- All verification scripts are correct and would pass against the proposed file contents

---

## Quick Wins

1. **Fix manifest format in Task 1.4** — use `{ "urls": { "https://api.open-meteo.com/...": "shenzhen-current.json" } }` to match existing mock infrastructure (T-1)
2. **Add `"open_meteo"` to `PROVIDERS` array in `test/setup.ts`** — extend Task 1.4 or create new task (T-2)
3. **Add `"open_meteo"` to `_PROVIDERS` tuple in `tests/conftest.py`** — extend Task 1.4 or create new task (T-3)
4. **Resolve PRD Non-Goals contradiction** — either remove "Python-runtime port" from Non-Goals or remove Tier 1B/4.2 from Tasks-003 (P-1)
5. **Fix BMKG priority in PRD table** — change from 9 to 8 to match `id_bmkg.py:85` (P-2)
6. **Add `observed_at` to Bun `parseCurrent`** — set from `current.time` ISO string (P-3)
7. **Add wind speed unit note to PRD** — document the km/h (Open-Meteo) vs m/s (OWM) cross-provider discrepancy (P-4)
8. **Update `weather/providers/__init__.py` docstring** — add Open-Meteo entry in Task 3.2 (T-5)
9. **Add comment for WMO code 66** — document the "Light freezing rain → rain" mapping choice in `wmo-codes.json` (P-6)
10. **Update PRD non-goal** — change "needs_capture: true" to "needs_capture: false" to match Task 1.4 (P-5)
