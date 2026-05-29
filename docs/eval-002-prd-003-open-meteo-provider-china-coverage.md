# Eval-002: PRD-003 + Tasks-003 Review — Open-Meteo Provider + China City Coverage

**Reviewed commits:**
- `122c7b1` — docs: add PRD-003 and tasks for Open-Meteo provider + China city coverage
- `eae3be1` — docs: apply eval-002 findings to PRD-003 and tasks-003

**Date:** 2026-05-29
**Status:** Open (pre-implementation)

---

## PRD-003 Document Review

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P-1 | **Critical** | Non-Goals stated *"Python-runtime port… a separate task"* but Tasks-003 included full Tier 1B (Python chain: tasks 3.1, 3.2) and Tier 2 task 4.2 (Python tests). | ✅ Fixed — `eae3be1` removed the "Python-runtime port" non-goal line. PRD now lists `open_meteo.py` as a new file and `bootstrap.py` / `providers/__init__.py` as modified files. |
| P-2 | Medium | Provider priority table listed BMKG at priority 9. Actual code: `weather/providers/id_bmkg.py:85` sets `priority = 8` (same as DWD). | ✅ Fixed — `eae3be1` corrected BMKG to priority 8. |
| P-3 | Medium | Bun `parseCurrent` sketch never set `observed_at`. Open-Meteo returns `current.time` (ISO timestamp). | ✅ Fixed — `eae3be1` updated the provider description to state `observed_at` is set from `new Date(current.time)`. |
| P-4 | Low | Wind speed unit inconsistency not acknowledged. Open-Meteo returns `wind_speed_10m` in km/h. OWM stores m/s (documented quirk in `openweathermap.ts`). The `WeatherData.wind_speed` field is documented as km/h in both runtimes. | ✅ Fixed — `eae3be1` added a **Wind speed unit note** blockquote in the Design section documenting the km/h (Open-Meteo) vs m/s (OWM) cross-provider discrepancy and that it pre-dates this PRD. |
| P-5 | Low | Non-Goals mentioned *"needs_capture: true"* for parity testing deferral, but Task 1.4 set `needs_capture: false`. | ✅ Fixed — `eae3be1` updated the parity non-goal to "fixture for Open-Meteo is hand-crafted with `needs_capture: false`". Also updated the Test Assets table to match. |
| P-6 | Low | WMO code 66 (`"66": "rain"`) maps "Light freezing rain" to `rain` rather than `sleet`. Defensible, but a brief comment in `wmo-codes.json` would document the mapping choice. | Open — cosmetic only, no code impact. |

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
| T-1 | **Critical** | Task 1.4 manifest format used `{ "responses": [...] }` but both `test/setup.ts` (line 64) and `tests/conftest.py` (line 35) expect `{ "urls": { "url": "file" } }`. | ✅ Fixed — `eae3be1` rewrote the manifest to `{ "urls": { ... } }` format. Added URL encoding note: commas in `current=` and `daily=` params are percent-encoded by `URLSearchParams`, so the manifest key uses `%2C`. Also updated the verify script to assert `'urls' in m`. |
| T-2 | **Critical** | No task updated `test/setup.ts` PROVIDERS array to include `"open_meteo"`. Without it, `loadFixtures()` skips the entire `fixtures/api-responses/open_meteo/` directory. | ✅ Fixed — `eae3be1` added step 3 to Task 1.4: append `"open_meteo"` to the `PROVIDERS` constant (line 29 of `test/setup.ts`). |
| T-3 | **Critical** | No task updated `tests/conftest.py` `_PROVIDERS` tuple to include `"open_meteo"`. The Python `mock_http` fixture only loaded manifests for 5 providers. | ✅ Fixed — `eae3be1` added step 4 to Task 1.4: add `"open_meteo"` to `_PROVIDERS` tuple in `tests/conftest.py` (line 21). |
| T-4 | Medium | Python `WeatherCondition(v)` call in `_WMO_CODE_MAP` construction raises `ValueError` at import time if a `wmo-codes.json` value is not a valid enum member. Unlike Bun's `buildConditionMap` (which uses `toCondition()` → silently falls through to `Unknown`), the Python side fails fast. | ✅ Acknowledged — `eae3be1` added a **Validation note** below the Task 3.1 code block stating this is intentional fail-fast behaviour: "a typo in the JSON will surface immediately rather than silently mapping to UNKNOWN. No change needed." |
| T-5 | Low | Task 3.2 did not mention updating `weather/providers/__init__.py`, which has a docstring listing all providers. | ✅ Fixed — `eae3be1` added steps to Task 3.2: (1) add docstring entry for `OpenMeteoProvider`, (2) add import, (3) add `__all__` entry. |
| T-6 | Low | Dependency graph text says Tier 2 tests "wait for Tier 1 + 1.4" but the graph visual shows no arrow from 1.4 to Tier 2. | Open — minor; textual description is authoritative. |

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

## Commit eae3be1 Verification

All 3 critical and 4 significant/medium items from the initial review are addressed:

| Original | Fix | Verified |
|----------|-----|----------|
| T-1 manifest format | Rewrote to `{ "urls": { ... } }` with `%2C` comma encoding | ✅ Matches `test/setup.ts:64` and `conftest.py:35` iteration pattern |
| T-2 `test/setup.ts` PROVIDERS | Step 3 added to Task 1.4 | ✅ `"open_meteo"` appended after `"tw_cwa"` |
| T-3 `tests/conftest.py` _PROVIDERS | Step 4 added to Task 1.4 | ✅ `"open_meteo"` appended to tuple |
| P-1 Non-Goals contradiction | Removed "Python-runtime port" line | ✅ PRD now lists `open_meteo.py`, `bootstrap.py`, `__init__.py` |
| P-2 BMKG priority | Corrected to 8 | ✅ Matches `id_bmkg.py:85` |
| P-3 observed_at | Added to provider description | ✅ `new Date(current.time)` documented |
| P-4 wind speed unit | Added blockquote note | ✅ km/h vs m/s discrepancy documented |
| P-5 needs_capture | Updated non-goal | ✅ `needs_capture: false` everywhere now |
| T-4 fail-fast validation | Added note | ✅ Documented as intentional |
| T-5 __init__.py | Added to Task 3.2 | ✅ Docstring + import + __all__ |

**Additional improvement verified:**
- Open Questions → Resolved Decisions — all 5 items now have explicit ✅ resolution statements
- PRD New Files table expanded to list both `open_meteo.ts` and `open_meteo.py`
- PRD Modified Files table expanded to list `bootstrap.py`, `__init__.py`, `setup.ts`, `conftest.py`
- PRD Test Assets table split into Bun and Python test files
- Fixed two broken verify-script code fences in tasks-003 (missing closing ` ``` `)

## Remaining Open Items

| # | Severity | Issue | Status |
|----------|----------|-------|--------|
| P-6 | Low | WMO code 66 mapping choice (`"66": "rain"` for "Light freezing rain") undocumented in `wmo-codes.json`. | Open — cosmetic |
| T-6 | Low | Dependency graph visual missing 1.4 → Tier 2 arrow. | Open — cosmetic |
| T-1 note | Medium | **URL encoding risk at implementation time** — the manifest key uses `%2C` for commas (matching `URLSearchParams` / `urllib.parse.urlencode`). The implementor must verify the actual URL string constructed by the provider matches the manifest key exactly. Recommend logging the URL from the mock 404 message on first test run and comparing. | Open — implementation-time guard |

## Quick Wins

1. ~~**Fix manifest format in Task 1.4**~~ ✅ Fixed in `eae3be1`
2. ~~**Add `"open_meteo"` to `PROVIDERS` array in `test/setup.ts`**~~ ✅ Fixed in `eae3be1`
3. ~~**Add `"open_meteo"` to `_PROVIDERS` tuple in `tests/conftest.py`**~~ ✅ Fixed in `eae3be1`
4. ~~**Resolve PRD Non-Goals contradiction**~~ ✅ Fixed in `eae3be1`
5. ~~**Fix BMKG priority in PRD table**~~ ✅ Fixed in `eae3be1`
6. ~~**Add `observed_at` to Bun `parseCurrent`**~~ ✅ Fixed in `eae3be1`
7. ~~**Add wind speed unit note to PRD**~~ ✅ Fixed in `eae3be1`
8. ~~**Update `weather/providers/__init__.py` docstring**~~ ✅ Fixed in `eae3be1`
9. **Add comment for WMO code 66** — document the "Light freezing rain → rain" mapping choice in `wmo-codes.json` (P-6)
10. ~~**Update PRD non-goal**~~ ✅ Fixed in `eae3be1`
