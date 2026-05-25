# Tasks for PRD-002: Bun Runtime Support (Dual-Package)

**PRD:** `docs/prd-002-bun-runtime-support.md`
**Created:** 2026-05-12
**Last reviewed:** 2026-05-17
**Scope:** v0.1 (Bun port for HKO, JMA, SG NEA, US NWS, OpenWeatherMap)

## Conventions

- ✅ — task complete
- ⏳ — task in progress
- (blank) — task not started
- **Parallel: yes** — task can be assigned to a sub-agent / junior dev concurrently with other "yes" tasks in the same phase
- **Parallel: no** — task gates the phase or depends on multiple prior tasks

## Dependency Graph

```
Phase 1 (data extraction + packaging) — must complete before any Bun work
  ┌─[1.1]──┐
  │ [1.2]  │
  │ [1.3]  ├──► [1.10]──► [1.11]──► [1.12]
  │ [1.4]  │     (loaders) (CLI fix) (CI/tests)
  │ [1.5]  │
  │ [1.6]  │
  │ [1.7]  │
  │ [1.8]  │
  │ [1.9]──┘
  (extract — all parallel)

Phase 2 (Bun scaffold)
  [2.1]  [2.2]  [2.3]   ← all parallel after Phase 1

Phase 3 (Bun providers + OWM) — all parallel after Phase 2
  [3.1 HKO]  [3.2 JMA]  [3.3 SG NEA]  [3.4 NWS]  [3.5 OWM]
                          │
                          └──► [3.6 bootstrap wiring]

Phase 5 (formatters + sender) — all parallel after Phase 2
  [5.1 utils]  [5.2 cli_text]  [5.3 telegram]  [5.4 whatsapp]  [5.5 sender]

Phase 6 (CLI + binary) — depends on Phase 3 + Phase 5
  [6.1 cli.ts] ──► [6.2 binary]

Phase 7 (tests + parity) — depends on Phase 6
  [7.1 fixtures]  [7.2 mock infra (Py)]  [7.3 mock infra (Bun)]
                                  │
                                  └──► [7.4 provider tests]  [7.5 formatter tests]  [7.6 cli tests]
                                                                          │
                                                                          └──► [7.7 cross-runtime parity]

Phase 8 (docs + release) — depends on Phase 7
  [8.1 SKILL.md]  [8.2 README]  [8.3 CHANGELOG]  ──► [8.4 GitHub release]
```

---

## Phase 1: Shared Data Extraction + Python Refactor

**Goal:** Move all hardcoded dicts from Python source into JSON files under `weather/data/`, refactor Python providers to load via `importlib.resources`, and prove the Python package still works.

**All extraction tasks (1.1–1.9) are independent and can be done in parallel by 9 different agents.** They only touch a single file each. Tasks 1.10–1.12 are gates run after all extractions complete.

### Task 1.1 ✅ — Extract `LOCATION_ALIASES` and `WeatherCondition` enum

**Files:**
- Read: `weather/models.py` (lines 12-58, 254-545)
- Create: `weather/data/__init__.py` (empty)
- Create: `weather/data/location-aliases.json`
- Create: `weather/data/weather-conditions.json`
- Create: `weather/data/condition-emoji.json`

**Depends on:** nothing
**Parallel:** yes (with 1.2–1.9)

**Steps:**

1. Create `weather/data/__init__.py` (empty file — makes the directory a Python package for `importlib.resources`).
2. Create `weather/data/location-aliases.json`: copy `LOCATION_ALIASES` dict from [`models.py:254-545`](file:///Users/karma/Developer/personal/weather-skill/weather/models.py#L254-L545) verbatim as JSON object. Preserve key ordering to ease diff review.
3. Create `weather/data/weather-conditions.json`: dump the 20 enum string values as a JSON array:
   ```json
   ["clear","sunny","partly_cloudy","cloudy","overcast","fog","mist","drizzle","rain","showers","heavy_rain","thunderstorm","snow","heavy_snow","sleet","hail","windy","hot","cold","unknown"]
   ```
4. Create `weather/data/condition-emoji.json`: dump `CONDITION_EMOJI` from [`models.py:37-58`](file:///Users/karma/Developer/personal/weather-skill/weather/models.py#L37-L58), keys as condition strings (not enum members):
   ```json
   {"clear":"☀️","sunny":"☀️","partly_cloudy":"⛅", ... }
   ```

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/location-aliases.json')); assert len(d) > 250 and 'hong kong' in d"
python -c "import json; assert len(json.load(open('weather/data/weather-conditions.json'))) == 20"
python -c "import json; assert json.load(open('weather/data/condition-emoji.json'))['clear'] == '☀️'"
```

---

### Task 1.2 ✅ — Extract HKO data

**Files:**
- Read: `weather/providers/hko.py` (lines 23-45)
- Create: `weather/data/condition-maps/__init__.py` (empty, may already exist if 1.3-1.9 created it first — `mkdir -p` semantics)
- Create: `weather/data/condition-maps/hko-icons.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Ensure `weather/data/condition-maps/__init__.py` exists (empty).
2. Create `weather/data/condition-maps/hko-icons.json` containing the `HKO_ICON_MAP` dict from [`hko.py:23-45`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/hko.py#L23-L45) with values as condition strings (not enum members):
   ```json
   {"pic50.png":"sunny","pic51.png":"sunny","pic52.png":"partly_cloudy", ... }
   ```

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/condition-maps/hko-icons.json')); assert d['pic50.png'] == 'sunny'"
```

---

### Task 1.3 ✅ — Extract JMA data

**Files:**
- Read: `weather/providers/jma.py` (lines 28-181)
- Create: `weather/data/cities/__init__.py` (empty)
- Create: `weather/data/cities/jma-area-codes.json`
- Create: `weather/data/condition-maps/jma-codes.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Ensure `weather/data/cities/__init__.py` and `weather/data/condition-maps/__init__.py` exist (empty).
2. Create `weather/data/cities/jma-area-codes.json` from `JMA_AREA_CODES` ([`jma.py:28-68`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/jma.py#L28-L68)).
3. Create `weather/data/condition-maps/jma-codes.json` from `JMA_WEATHER_CODE_MAP` ([`jma.py:72-181`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/jma.py#L72-L181)) with condition string values (not enum members).

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/cities/jma-area-codes.json')); assert d['tokyo'] == '130000'"
python -c "import json; d=json.load(open('weather/data/condition-maps/jma-codes.json')); assert d['100'] == 'sunny' and len(d) >= 100"
```

---

### Task 1.4 ✅ — Extract US NWS data

**Files:**
- Read: `weather/providers/us_nws.py`
- Create: `weather/data/cities/us-nws.json`
- Create: `weather/data/condition-maps/nws-conditions.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Locate `US_CITIES` dict in `us_nws.py` (~lines 27-78).
2. Locate `NWS_CONDITION_MAP` dict in `us_nws.py` (~lines 81-123).
3. Create `weather/data/cities/us-nws.json` and `weather/data/condition-maps/nws-conditions.json`.
4. Convert all `WeatherCondition.X` values to their string equivalents.

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/cities/us-nws.json')); assert 'new york' in d"
python -c "import json; d=json.load(open('weather/data/condition-maps/nws-conditions.json')); assert len(d) >= 30"
```

---

### Task 1.5 ✅ — Extract SG NEA data

**Files:**
- Read: `weather/providers/sg_nea.py`
- Create: `weather/data/condition-maps/sg-nea-forecast.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Locate `SG_CONDITION_MAP` in `sg_nea.py` (~lines 29-53).
2. Create `weather/data/condition-maps/sg-nea-forecast.json` with condition string values.

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/condition-maps/sg-nea-forecast.json')); assert len(d) >= 20"
```

---

### Task 1.6 ✅ — Extract DWD data

**Files:**
- Read: `weather/providers/de_dwd.py`
- Create: `weather/data/cities/de-dwd.json`
- Create: `weather/data/condition-maps/brightsky-conditions.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Locate `DE_CITIES` (~lines 28-58) and `BRIGHTSKY_CONDITION_MAP` (~lines 62-76).
2. Create the two JSON files.

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/cities/de-dwd.json')); assert 'berlin' in d"
```

---

### Task 1.7 ✅ — Extract OpenWeatherMap data

**Files:**
- Read: `weather/providers/openweathermap.py`
- Create: `weather/data/condition-maps/owm-codes.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Locate `CONDITION_MAP` in `openweathermap.py` (~lines 30-94).
2. Create `weather/data/condition-maps/owm-codes.json` with **string keys** (OWM uses integer codes; JSON keys must be strings — convert each int key to its string representation).

**Verify:**
```bash
python -c "import json; d=json.load(open('weather/data/condition-maps/owm-codes.json')); assert d['200'] == 'thunderstorm'"
```

---

### Task 1.8 ✅ — Extract batch-2 condition maps (CWA, Met Office, BOM, MetService)

**Files:**
- Read: `weather/providers/{tw_cwa,uk_metoffice,au_bom,nz_metservice}.py`
- Create: `weather/data/condition-maps/{cwa,metoffice,bom,metservice}-conditions.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

For each of the 4 providers, locate the condition-map dict and any city-coordinate dict. Extract to JSON. (Even though batch-2 providers aren't ported to Bun in v0.1, extracting the data now de-risks PRD-002b.)

**Verify:**
```bash
ls weather/data/condition-maps/cwa-conditions.json weather/data/condition-maps/metoffice-conditions.json weather/data/condition-maps/bom-conditions.json weather/data/condition-maps/metservice-conditions.json
```

---

### Task 1.9 ✅ — Extract batch-2 condition maps (BMKG, KMA, TMD)

**Files:**
- Read: `weather/providers/{id_bmkg,kr_kma,th_tmd}.py`
- Create: `weather/data/condition-maps/{bmkg,kma,tmd}-conditions.json` (and any city files if present)

**Depends on:** nothing
**Parallel:** yes

**Steps:**

Same pattern as 1.8 for the remaining 3 providers.

**Verify:**
```bash
ls weather/data/condition-maps/bmkg-conditions.json weather/data/condition-maps/kma-conditions.json weather/data/condition-maps/tmd-conditions.json
```

---

### Task 1.10 ✅ — Switch Python providers + models to load from JSON

**Files (modify in place):**
- `weather/models.py`
- `weather/providers/hko.py`
- `weather/providers/jma.py`
- `weather/providers/us_nws.py`
- `weather/providers/sg_nea.py`
- `weather/providers/de_dwd.py`
- `weather/providers/openweathermap.py`
- `weather/providers/{tw_cwa,uk_metoffice,au_bom,nz_metservice,id_bmkg,kr_kma,th_tmd}.py`

**Depends on:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9
**Parallel:** no (gate)

**Steps:**

1. Add a small helper in a new module `weather/data/loader.py`:
   ```python
   from importlib.resources import files
   import json
   from typing import Any

   def load_json(*path_parts: str) -> Any:
       """Load a JSON file from weather/data/."""
       resource = files("weather.data").joinpath(*path_parts)
       return json.loads(resource.read_text(encoding="utf-8"))
   ```
2. In each modified file, replace the hardcoded dict with a loader call. Example for `hko.py`:
   ```python
   from ..data.loader import load_json

   _RAW = load_json("condition-maps", "hko-icons.json")
   HKO_ICON_MAP = {k: WeatherCondition(v) for k, v in _RAW.items()}
   ```
3. For `models.py`, similarly load `LOCATION_ALIASES` and rebuild `CONDITION_EMOJI`:
   ```python
   from .data.loader import load_json
   LOCATION_ALIASES = load_json("location-aliases.json")
   _EMOJI_RAW = load_json("condition-emoji.json")
   CONDITION_EMOJI = {WeatherCondition(k): v for k, v in _EMOJI_RAW.items()}
   ```
4. Module-level eager loading is fine — matches current import-time semantics.

**Verify:**
```bash
python -c "from weather.providers.hko import HKO_ICON_MAP; from weather.models import WeatherCondition; assert HKO_ICON_MAP['pic50.png'] == WeatherCondition.SUNNY"
python -c "from weather.models import LOCATION_ALIASES, CONDITION_EMOJI, WeatherCondition; assert 'hong kong' in LOCATION_ALIASES; assert CONDITION_EMOJI[WeatherCondition.SUNNY] == '☀️'"
```

---

### Task 1.11 ✅ — Update `pyproject.toml` for package data + fix CLI JSON output

**Files:**
- `pyproject.toml`
- `weather/cli.py`

**Depends on:** 1.10
**Parallel:** no

**Steps:**

1. Add to `pyproject.toml`:
   ```toml
   [tool.setuptools]
   packages = ["weather", "weather.providers", "weather.formatters", "weather.senders", "weather.data"]

   [tool.setuptools.package-data]
   "weather.data" = ["*.json", "**/*.json"]
   ```
2. Modify [`weather/cli.py`](file:///Users/karma/Developer/personal/weather-skill/weather/cli.py) JSON output (line 135):
   ```python
   print(json.dumps(
       output,
       indent=2,
       sort_keys=True,
       default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o),
   ))
   ```

**Verify:**
```bash
python -m weather.cli --location "Hong Kong" --format json | python -c "import sys,json; d=json.load(sys.stdin); assert 'temperature' in d and 'provider_name' in d"
```

---

### Task 1.12 ✅ — Run existing Python test suite + add wheel CI smoke test

**Files:**
- `tests/` (existing)
- `.github/workflows/` (add or update CI)

**Depends on:** 1.10, 1.11
**Parallel:** no (gate — validates all of Phase 1)

**Steps:**

1. Run `pytest tests/ -v` and confirm zero regressions. (If a test mocks the old hardcoded dicts directly, fix the test to use the new loader path or assert against the loaded values.)
2. Add a CI step that builds the wheel and verifies JSON files are included:
   ```yaml
   - name: Verify wheel ships data files
     run: |
       pip install build
       python -m build --wheel
       count=$(unzip -l dist/*.whl | grep -c 'weather/data/.*\.json')
       echo "JSON files in wheel: $count"
       test "$count" -ge 15
   ```
3. Smoke test the installed wheel:
   ```bash
   python -m venv /tmp/wheel-test
   /tmp/wheel-test/bin/pip install dist/*.whl
   /tmp/wheel-test/bin/python -c "from weather.providers.hko import HKO_ICON_MAP; print(len(HKO_ICON_MAP))"
   ```

**Verify:**
- All existing pytest cases pass.
- `python -m build --wheel` succeeds and the wheel contains all `weather/data/**/*.json`.

---

## Phase 2: Bun Scaffold + Core Types

### Task 2.1 ✅ — Create `package.json`, `tsconfig.json`, `bunfig.toml`

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `bunfig.toml`
- Create: `.gitignore` additions for `node_modules/`, `dist/`, `weather`

**Depends on:** Phase 1
**Parallel:** yes (with 2.2, 2.3)

**Steps:**

1. `package.json`:
   ```json
   {
     "name": "@shrwnsan/weather-skill",
     "version": "0.1.0-pre.1",
     "type": "module",
     "engines": { "bun": ">=1.1.30" },
     "main": "src/index.ts",
     "bin": { "weather": "src/cli.ts" },
     "files": ["src/", "weather/data/"],
     "scripts": {
       "test": "bun test",
       "build": "bun build src/cli.ts --compile --target=bun-linux-x64 --outfile weather"
     }
   }
   ```
2. `tsconfig.json` (strict, ESNext target, `bun-types`):
   ```json
   {
     "compilerOptions": {
       "target": "ESNext",
       "module": "ESNext",
       "moduleResolution": "bundler",
       "strict": true,
       "esModuleInterop": true,
       "resolveJsonModule": true,
       "types": ["bun"]
     },
     "include": ["src/", "test/"]
   }
   ```
3. `bunfig.toml` (minimal):
   ```toml
   [test]
   preload = ["./test/setup.ts"]
   ```

**Verify:**
```bash
bun install
bun --version  # ensure >= 1.1.30
```

---

### Task 2.2 ✅ — Create core types in `src/types.ts`

**File:** `src/types.ts`
**Depends on:** Phase 1
**Parallel:** yes

**Steps:**

1. Define `WeatherCondition` enum (20 values, snake_case string values matching `weather/data/weather-conditions.json`).
2. Define `WeatherData` interface (snake_case fields per "JSON Schema Parity" section of PRD).
3. Define `Location` interface.
4. Define `IWeatherProvider`, `IWeatherFormatter`, `IWeatherSender` interfaces (method names camelCase — these don't appear in JSON).
5. Define `SendOptions`, `SendResult` interfaces.
6. Add `// eslint-disable @typescript-eslint/naming-convention` at top.

**Verify:**
```bash
bunx tsc --noEmit
```

---

### Task 2.3 ✅ — Create `src/data-loader.ts` and `src/models.ts`

**Files:**
- Create: `src/data-loader.ts`
- Create: `src/models.ts`

**Depends on:** Phase 1, 2.2
**Parallel:** yes (with 2.1; depends on 2.2)

**Steps:**

1. `src/data-loader.ts`: utility to read JSON from `weather/data/`. Use `Bun.file()` for runtime reads but `import` JSON directly so it gets bundled into the compiled binary:
   ```typescript
   import locationAliases from "../weather/data/location-aliases.json";
   import conditionEmoji from "../weather/data/condition-emoji.json";
   // ... etc
   export { locationAliases, conditionEmoji };
   ```
2. `src/models.ts`: helper functions mirroring Python's `models.py` properties — `humidityStr(data)`, `windStr(data)`, `tempRangeStr(data)`, `aqhiStr(data)`, `aqiStr(data)`, `effectiveFeelsLike(data)`, `calculateFeelsLike(temp, humidity, windSpeed)`, `normalizeLocation(raw)`, `parseLocation(raw)`, `getEmoji(condition)`.

**Verify:**
```bash
bunx tsc --noEmit
bun -e 'import { calculateFeelsLike } from "./src/models"; console.log(calculateFeelsLike(30, 80, 0))'
```

---

## Phase 3: Bun Providers (Batch 1 + OWM)

All 5 provider tasks are independent and can be assigned to 5 different agents.

### Task 3.1 ✅ — Port HKOProvider

**File:** `src/providers/hko.ts`
**Reference:** [`weather/providers/hko.py`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/hko.py)
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

1. Implement `HKOProvider implements IWeatherProvider`.
2. Load `HKO_ICON_MAP` via `data-loader`.
3. Implement `supportsLocation`, `getCurrent`, `getForecast` mirroring [`hko.py`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/hko.py).
4. Use native `fetch()` (no User-Agent needed for HKO).
5. Helpers: `iconToCondition`, `psrToPercent`, `stripHtmlTags`.

**Verify:**
```bash
bun -e 'import { HKOProvider } from "./src/providers/hko"; const p = new HKOProvider(); const d = await p.getCurrent({ raw: "Hong Kong", normalized: "hong kong" }); console.log(d.temperature, d.provider_name)'
```

---

### Task 3.2 ✅ — Port JMAProvider

**File:** `src/providers/jma.ts`
**Reference:** [`weather/providers/jma.py`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/jma.py)
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

1. Implement `JMAProvider`.
2. Load `JMA_AREA_CODES`, `JMA_WEATHER_CODE_MAP` via `data-loader`.
3. **Set `User-Agent: WeatherSkill/1.0`** on all `fetch()` calls (matches [`jma.py:278`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/jma.py#L278)).
4. Two endpoints: forecast + overview. Same parsing as Python (3-level nested timeSeries traversal).

**Verify:**
```bash
bun -e 'import { JMAProvider } from "./src/providers/jma"; const p = new JMAProvider(); const d = await p.getCurrent({ raw: "Tokyo", normalized: "tokyo" }); console.log(d.location, d.temperature)'
```

---

### Task 3.3 ✅ — Port SGNEAProvider

**File:** `src/providers/sg_nea.ts`
**Reference:** [`weather/providers/sg_nea.py`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/sg_nea.py)
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

1. Implement `SGNEAProvider`.
2. Load `SG_CONDITION_MAP` via `data-loader`.
3. NEA API: `https://api-open.data.gov.sg/v2/real-time/api/...`.

**Verify:**
```bash
bun -e 'import { SGNEAProvider } from "./src/providers/sg_nea"; const p = new SGNEAProvider(); const d = await p.getCurrent({ raw: "Singapore", normalized: "singapore" }); console.log(d.temperature)'
```

---

### Task 3.4 ✅ — Port NWSProvider

**File:** `src/providers/us_nws.ts`
**Reference:** [`weather/providers/us_nws.py`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/us_nws.py)
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

1. Implement `NWSProvider`.
2. Load `US_CITIES`, `NWS_CONDITION_MAP` via `data-loader`.
3. **CRITICAL:** NWS requires `User-Agent` header with contact email. Match the exact header from `us_nws.py`. Without this, NWS returns 403.
4. Multi-step fetch: `/points/{lat},{lon}` → resolves to forecast URL → fetch forecast.

**Verify:**
```bash
bun -e 'import { NWSProvider } from "./src/providers/us_nws"; const p = new NWSProvider(); const d = await p.getCurrent({ raw: "New York", normalized: "new york" }); console.log(d.temperature)'
```

---

### Task 3.5 ✅ — Port OpenWeatherMapProvider

**File:** `src/providers/openweathermap.ts`
**Reference:** [`weather/providers/openweathermap.py`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/openweathermap.py)
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

1. Implement `OpenWeatherMapProvider` with `apiKey` constructor arg.
2. Load `CONDITION_MAP` (string-keyed integer codes) via `data-loader`.
3. Geocoding endpoint to resolve location → lat/lon, then `/data/2.5/weather` and `/data/2.5/forecast`.

**Verify:**
```bash
OPENWEATHERMAP_API_KEY=xxx bun -e 'import { OpenWeatherMapProvider } from "./src/providers/openweathermap"; const p = new OpenWeatherMapProvider(process.env.OPENWEATHERMAP_API_KEY!); const d = await p.getCurrent({ raw: "London", normalized: "london" }); console.log(d.temperature)'
```

---

### Task 3.6 ✅ — Wire providers into `src/bootstrap.ts`

**Files:** `src/bootstrap.ts`, `src/skill.ts`, `src/index.ts`
**Depends on:** 3.1, 3.2, 3.3, 3.4, 3.5
**Parallel:** no

**Steps:**

1. Mirror [`weather/bootstrap.py`](file:///Users/karma/Developer/personal/weather-skill/weather/bootstrap.py): `buildDefaultSkill()` registers HKO, SG NEA, JMA, NWS unconditionally, OWM only if `process.env.OPENWEATHERMAP_API_KEY` is set.
2. Sort by `priority`.
3. Export `WeatherSkill` class with same interface as Python.

**Implementation notes:**

- `src/skill.ts` contains the `WeatherSkill` orchestrator (mirrors `weather/skill.py`): `getCurrent`, `getForecast`, `format`, `send`, `addProvider`, `addFormatter`, `addSender`, plus read-only `providers` / `platforms` / `channels` views. Includes a built-in plain-text fallback formatter for the case where no formatter is registered for the requested platform (matches Python's `_format_simple`).
- `src/index.ts` is the public package entry point (`main` in `package.json`); re-exports the orchestrator, factory, types, providers, and model helpers.
- `buildFormatters()` and `buildSenders()` return empty maps for now. Phase 5 will populate them with `CliTextFormatter`, `TelegramFormatter`, `WhatsAppFormatter`, and `TelegramSender`.

**Verify:**
```bash
bun -e 'import { buildDefaultSkill } from "./src/bootstrap"; const s = buildDefaultSkill(); console.log(s.providers.map(p => p.name))'
# Expected: ["hko","sg_nea","jma","nws"]  (+ "openweathermap" if API key set)
# Note: the US provider's `name` is "nws" (matches Python — see weather/providers/us_nws.py:71),
# even though the file is `src/providers/us_nws.ts`.
```

---

## Phase 5: Bun Formatters + Sender

### Task 5.1 ✅ — Create `src/utils.ts` (shared formatter helpers)

**File:** `src/utils.ts`
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

Port the helper functions from Python's [`telegram.py`](file:///Users/karma/Developer/personal/weather-skill/weather/formatters/telegram.py) and `whatsapp.py`:
- `aqhiQuality(aqhi: number): string`
- `uvDescription(uv: number): string`
- `generateSummary(data: WeatherData): string`

**Verify:**
```bash
bun -e 'import { aqhiQuality } from "./src/utils"; console.log(aqhiQuality(5))'  # "Moderate"
```

---

### Task 5.2 ✅ — Port CliTextFormatter

**File:** `src/formatters/cli_text.ts`
**Reference:** [`weather/formatters/cli_text.py`](file:///Users/karma/Developer/personal/weather-skill/weather/formatters/cli_text.py)
**Depends on:** Phase 2, 5.1
**Parallel:** yes

**Steps:**

Implement `CliTextFormatter implements IWeatherFormatter` with `platform = "text"`.

---

### Task 5.3 ✅ — Port TelegramFormatter

**File:** `src/formatters/telegram.ts`
**Reference:** [`weather/formatters/telegram.py`](file:///Users/karma/Developer/personal/weather-skill/weather/formatters/telegram.py)
**Depends on:** Phase 2, 5.1
**Parallel:** yes

**Steps:**

1. Implement `TelegramFormatter`.
2. **Use the exact escape character set** from [`telegram.py:15`](file:///Users/karma/Developer/personal/weather-skill/weather/formatters/telegram.py#L15): `r'_*[]()~`>#+-=|{}.!'` — store as a constant.
3. Implement `escapeMdv2(text)` and `formatCurrent(data)`.

---

### Task 5.4 ✅ — Port WhatsAppFormatter

**File:** `src/formatters/whatsapp.ts`
**Reference:** [`weather/formatters/whatsapp.py`](file:///Users/karma/Developer/personal/weather-skill/weather/formatters/whatsapp.py)
**Depends on:** Phase 2, 5.1
**Parallel:** yes

**Steps:**

Implement `WhatsAppFormatter`.

---

### Task 5.5 ✅ — Port TelegramSender

**File:** `src/senders/telegram.ts`
**Reference:** [`weather/senders/telegram.py`](file:///Users/karma/Developer/personal/weather-skill/weather/senders/telegram.py)
**Depends on:** Phase 2
**Parallel:** yes

**Steps:**

1. Implement `TelegramSender implements IWeatherSender`.
2. Read `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` from `process.env`.
3. POST to `https://api.telegram.org/bot{token}/sendMessage` with `parse_mode: "MarkdownV2"`.
4. Return `SendResult` matching Python's shape.

---

## Phase 6: Bun CLI + Compiled Binary

### Task 6.1 ✅ — Implement `src/cli.ts` with arg parsing

**File:** `src/cli.ts`
**Depends on:** Phase 3, Phase 5
**Parallel:** no

**Steps:**

1. Inline arg parser for the 9 flags (no external deps). Match Python's defaults and edge-case behavior:
   - `--send` + `--format json` → exit 2 with stderr error
   - `--provider <unknown>` → list available providers, exit 1
2. JSON output with `sort_keys` walker + ISO-8601 datetime (per PRD JSON Schema Parity section).
3. Mirror [`weather/cli.py:main()`](file:///Users/karma/Developer/personal/weather-skill/weather/cli.py#L102-L160) flow.

**Verify:**
```bash
bun run src/cli.ts --location "Hong Kong"
bun run src/cli.ts --location "Hong Kong" --format json | jq .temperature
```

---

### Task 6.2 ✅ — Build compiled binary + verify size

**Depends on:** 6.1
**Parallel:** no

**Steps:**

1. Run `bun build src/cli.ts --compile --target=bun-linux-x64 --outfile weather-linux-x64` (the outfile must NOT be `weather` — it collides with the existing `weather/` Python package directory).
2. Verify `./weather-linux-x64 --location "Hong Kong"` works on a Linux container (e.g. via `docker run --rm -v $(pwd):/w alpine /w/weather-linux-x64 --location "Hong Kong"` — note: requires glibc, may need `--target=bun-linux-x64-musl` for Alpine).
3. Verify size < 150MB. If larger, escalate to NanoClaw team for ceiling confirmation.

**Verify:**
```bash
ls -lh weather-linux-x64
file weather-linux-x64
```

---

## Phase 7: Bun Tests + Cross-Runtime Parity

### Task 7.1 ✅ — Create fixtures directory + manifest format

**Files:**
- Create: `fixtures/api-responses/{hko,jma,sg_nea,us_nws,openweathermap}/manifest.json`
- Create: captured response files for each provider
- Update: `MANIFEST.in` (exclude `fixtures/`); update `package.json` `files` to exclude

**Depends on:** Phase 6
**Parallel:** yes (with 7.2, 7.3)

**Steps:**

1. Manually capture one current + one forecast response per provider via `curl` (or replay from existing tests if available).
2. Create per-provider `manifest.json` mapping URLs → relative file paths.
3. For OWM, replace API key in URL with `<API_KEY>` placeholder.

---

### Task 7.2 ✅ — Python mock infrastructure (`tests/conftest.py`)

**File:** `tests/conftest.py`
**Depends on:** 7.1
**Parallel:** yes (with 7.3)

**Steps:**

1. Add `mock_http` pytest fixture that:
   - Loads manifests for all providers.
   - Patches `urllib.request.urlopen` to look up requested URL → return `BytesIO(canned_bytes)`.
2. Add `frozen_clock` fixture using `freezegun` (add to dev deps) → freezes to `2026-01-01T00:00:00+00:00`.

---

### Task 7.3 ✅ — Bun mock infrastructure (`test/setup.ts`)

**File:** `test/setup.ts`
**Depends on:** 7.1
**Parallel:** yes

**Steps:**

1. Implement a fixture-backed `fetch` mock using Bun's `mock.module()`.
2. Implement clock freezing (`Date` mock or injected clock).
3. Loaded via `bunfig.toml` `[test] preload`.

---

### Task 7.4 ✅ — Provider tests (5 files, parallel)

**Files:**
- `test/providers/hko.test.ts`
- `test/providers/jma.test.ts`
- `test/providers/sg_nea.test.ts`
- `test/providers/us_nws.test.ts`
- `test/providers/openweathermap.test.ts`

**Depends on:** 7.3
**Parallel:** yes (each file can be a separate agent)

**Steps:**

For each provider, write tests that:
1. Use `mockFetch` to replay the fixture.
2. Call `getCurrent` and `getForecast`.
3. Assert key fields match expected values from the canned response.

---

### Task 7.5 ✅ — Formatter tests

**Files:**
- `test/formatters/cli_text.test.ts`
- `test/formatters/telegram.test.ts`
- `test/formatters/whatsapp.test.ts`

**Depends on:** Phase 5
**Parallel:** yes

**Steps:**

Snapshot tests for each formatter against a fixed `WeatherData` input.

---

### Task 7.6 ✅ — CLI integration tests

**File:** `test/cli.test.ts`
**Depends on:** Phase 6, 7.3
**Parallel:** yes

**Steps:**

1. Test `--location "Hong Kong"` produces text output.
2. Test `--format json` produces sorted-key JSON.
3. Test `--send --format json` returns exit code 2.
4. Test `--provider unknown` returns exit code 1 with provider list.

---

### Task 7.7 ✅ — Cross-runtime JSON parity test

**Files:**
- `test/parity.test.ts` (Bun side)
- `tests/test_parity.py` (Python side)
- `.github/workflows/parity.yml` (CI)

**Depends on:** 7.4, 7.6, Phase 1
**Parallel:** no (gate)

**Steps:**

1. For each of the 5 v0.1 providers:
   - Run Python CLI with mocked HTTP + frozen clock → capture JSON output.
   - Run Bun CLI with same fixture + frozen clock → capture JSON output.
   - Diff byte-by-byte. Assert equal.
2. Wire into CI to run on every PR.

---

## Phase 8: Docs + GitHub Release

### Task 8.1 ✅ — Update SKILL.md

**File:** `SKILL.md`
**Depends on:** Phase 7
**Parallel:** yes

**Steps:**

1. Update frontmatter `compatibility:` to mention both Python and Bun runtimes.
2. Replace stale "NanoClaw" Python integration with Bun snippet (per PRD §SKILL.md Updates).
3. Add list of v0.1 providers (5) vs deferred providers (8).
4. Document compiled binary distribution.

---

### Task 8.2 ✅ — Update README

**File:** `README.md`
**Depends on:** Phase 7
**Parallel:** yes

**Steps:**

Add Bun installation instructions, compiled binary download link, Bun usage examples.

---

### Task 8.3 ✅ — Update CHANGELOG

**File:** `CHANGELOG.md`
**Depends on:** Phase 7
**Parallel:** yes

**Steps:**

Add `## [0.1.0-bun] - 2026-XX-XX` entry summarizing the Bun port.

---

### Task 8.4 — Tag and release `v0.1.0-bun`

**Depends on:** 8.1, 8.2, 8.3, 6.2
**Parallel:** no

**Steps:**

1. `git tag v0.1.0-bun`
2. `git push origin v0.1.0-bun`
3. Create GitHub release with the compiled `weather-linux-x64` binary attached.
4. Notify NanoClaw team.

---

## Out of Scope (PRD-002b — fast-follow)

- Phase 4 (batch-2 providers): CWA, Met Office, BOM, MetService, BMKG, DWD, KMA, TMD
- npm publish to public registry
- Cross-platform binary builds (`bun-darwin-arm64`, `bun-darwin-x64`, `bun-windows-x64`)
- Python `utils.py` formatter deduplication refactor
