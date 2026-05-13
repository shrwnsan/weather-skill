# PRD-002: Bun Runtime Support (Dual-Package)

**Status:** Draft
**Created:** 2026-05-12
**Priority:** High
**Release Strategy:** Incremental (Option B) — v0.1 ships batch-1 providers + OpenWeatherMap fallback; batch-2 providers ship in a fast-follow PRD-002b.

## Scope & Release Strategy

Two Bun releases instead of one big-bang port:

| Release | Providers | ETA | Goal |
|---------|-----------|-----|------|
| **`@shrwnsan/weather-skill@0.1.0`** (this PRD) | HKO, JMA, SG NEA, US NWS, **+ OpenWeatherMap (global fallback)** | ~15h | Unblock NanoClaw immediately. Locations not covered by the 4 regional providers fall through to OWM (degraded but functional). |
| **`@shrwnsan/weather-skill@1.0.0`** (PRD-002b) | + CWA, Met Office, BOM, MetService, BMKG, DWD, KMA, TMD | ~25h additional | Full feature parity with Python package. |

**Rationale:** the 4 batch-1 providers cover HK, Japan, Singapore, and USA — historically the highest-traffic regions for the existing Python skill. OpenWeatherMap covers everywhere else with reduced fidelity (no AQHI, generic icons). Shipping v0.1 in ~15h delivers measurable value to NanoClaw 25h sooner than waiting for the full 13-provider port, and gives us a real production signal before committing to batch 2.

**Phase-0 decisions locked in:**
- ✅ Data packaging: **Option A** (`weather/data/`)
- ✅ JSON schema: **snake_case throughout TypeScript** (matches Python; no transform shim)
- ✅ Scope: **Option B** (incremental — v0.1 batch-1 + OWM, then PRD-002b for batch-2)
- ✅ Test fixtures: **`fixtures/api-responses/<provider>/`** at repo root with per-provider `manifest.json` mapping URLs → response files; both runtimes load via relative paths; excluded from wheel (`MANIFEST.in`) and npm (`files` whitelist).
- ✅ **Clock mocking in parity tests**: both runtimes freeze `datetime.now()` / `new Date()` to `2026-01-01T00:00:00Z` so `fetched_at` and other time-dependent fields don't cause spurious diffs.
- ✅ **Sorted JSON keys**: both runtimes emit `--format json` with sorted keys (`json.dumps(..., sort_keys=True)` in Python; equivalent walker in Bun) to eliminate field-ordering fragility from `dataclasses.asdict()` declaration order vs JS object insertion order.

## Problem Statement

The weather skill is Python-only. NanoClaw agent runs Docker without Python 3, requiring significant architecture changes to support Python. Running Bun (a single-binary JS/TS runtime) would make the skill immediately usable by NanoClaw without Docker modifications.

> **Note (verified 2026-05-12):** The current [`SKILL.md`](file:///Users/karma/Developer/personal/weather-skill/SKILL.md) "Integration → NanoClaw" section already documents a Python integration (`from weather import WeatherSkill ...`). That section is stale relative to the actual NanoClaw runtime described above and must be updated as part of Phase 8.

The broader agent ecosystem spans two runtime worlds:

| Agent | Runtime | Current Integration | Blocker |
|-------|---------|-------------------|---------|
| OpenClaw | Python | `from weather import WeatherSkill` | None — works today |
| Hermes Agent | Python | Same as OpenClaw | None — works today |
| NanoClaw | Bun/Docker (no Python) | None | No Python in container |
| Future agents | Unknown | — | Unknown runtime requirements |

A Bun-only rewrite would break Python agents. A Python-only approach leaves NanoClaw blocked. A dual-package with shared data is the correct tradeoff.

## Goals

### v0.1 Goals (this PRD)

1. **Bun/TypeScript implementation of batch-1 providers** — HKO, JMA, SG NEA, US NWS + OpenWeatherMap (global fallback); 3 formatters (cli_text, telegram, whatsapp); Telegram sender; CLI.
2. **Shared data layer** — extract ~1,300 lines of pure data (location aliases, condition maps, city coordinates) into language-agnostic JSON so both packages consume the same source of truth. **All 13 providers' maps are extracted in Phase 1**, even though only 5 are wired into the Bun package in v0.1 — this de-risks PRD-002b and avoids a second round of Python refactoring.
3. **Compiled binary distribution** — `bun build --compile` produces a single `weather` binary for agents that can't install packages (NanoClaw Docker).
4. **Identical CLI interface** — same flags, same output, regardless of runtime. JSON output uses **snake_case** in both runtimes (decision: TS adopts Python's convention to eliminate the transform shim).
5. **Updated SKILL.md** — document both Python and Bun integration patterns; replace stale NanoClaw Python snippet with the Bun snippet; clearly mark which 4 regional providers are batch-1 and which 8 are deferred to batch-2.
6. **Zero disruption to existing Python users** — `from weather import WeatherSkill` continues to work unchanged, and `pip install weather-skill` continues to ship all required data files (resolved via Option A in *Data Packaging*).

### Deferred to PRD-002b (v1.0)

7. Bun ports of CWA, Met Office, BOM, MetService, BMKG, DWD, KMA, TMD providers (~25h).
8. npm publish to public registry (v0.1 distributed via GitHub release + compiled binary; npm publish gated on production signal from NanoClaw).

## Non-Goals

- Replacing the Python package. Both packages are first-class and maintained.
- Adding new providers, formatters, or senders (that's a separate PRD).
- Building a shared library / FFI bridge between Python and Bun (over-engineering).
- npm package publishing (can be added later; compiled binary covers the immediate NanoClaw case).
- Supporting Node.js specifically (Bun is the target runtime; Node compat is a nice-to-have, not a requirement).
- Python→TypeScript transpilation tools (the port is manual for correctness).

## Design

### Repository Structure

> **Recommended layout (Option A from *Data Packaging*):** shared JSON lives inside `weather/data/` so the Python wheel ships it automatically. Bun reads from the same directory.

```
weather-skill/
├── weather/                           # Python package (existing, ~7,300 lines)
│   ├── data/                          # Shared data (language-agnostic JSON)
│   │   ├── __init__.py                # makes resource discoverable via importlib.resources
│   │   ├── weather-conditions.json    # 20 canonical WeatherCondition values
│   │   ├── location-aliases.json      # ~290 city aliases (9 regions, 3 scripts)
│   │   ├── condition-emoji.json       # 20 WeatherCondition → emoji mappings (verified)
│   │   ├── cities/
│   │   │   ├── __init__.py
│   │   │   ├── us-nws.json
│   │   │   ├── de-dwd.json
│   │   │   └── jma-area-codes.json    # ~25 JMA areas (verified)
│   │   └── condition-maps/
│   │       ├── __init__.py
│   │       ├── hko-icons.json
│   │       ├── jma-codes.json         # ~100 JMA 3-digit codes (verified)
│   │       ├── nws-conditions.json
│   │       ├── sg-nea-forecast.json
│   │       ├── owm-codes.json
│   │       ├── brightsky-conditions.json
│   │       ├── cwa-conditions.json    # NEW — Phase 1 also extracts these
│   │       ├── metoffice-conditions.json
│   │       ├── bom-conditions.json
│   │       ├── metservice-conditions.json
│   │       ├── bmkg-conditions.json
│   │       ├── kma-conditions.json
│   │       └── tmd-conditions.json
│   ├── models.py                      # Updated: loads LOCATION_ALIASES via importlib.resources
│   ├── providers/                     # Existing providers, updated to load maps from data/
│   │   ├── hko.py                     # Load HKO_ICON_MAP from data/
│   │   ├── jma.py                     # Load JMA_WEATHER_CODE_MAP + JMA_AREA_CODES from data/
│   │   ├── us_nws.py                  # Load US_CITIES + NWS_CONDITION_MAP from data/
│   │   ├── sg_nea.py                  # Load SG_CONDITION_MAP from data/
│   │   ├── de_dwd.py                  # Load DE_CITIES + BRIGHTSKY_CONDITION_MAP from data/
│   │   └── openweathermap.py          # Load CONDITION_MAP from data/
│   ├── formatters/                    # Unchanged
│   ├── senders/                       # Unchanged
│   ├── skill.py                       # Unchanged
│   ├── bootstrap.py                   # Unchanged
│   └── cli.py                         # Unchanged
│
├── src/                               # Bun/TypeScript package (new)
│   ├── index.ts                       # Package exports (WeatherSkill class)
│   ├── cli.ts                         # CLI entry point
│   ├── models.ts                      # WeatherData, Location, WeatherCondition types
│   ├── bootstrap.ts                   # buildDefaultSkill() factory
│   ├── utils.ts                       # Shared formatter utils (AQHI quality, UV description, summary generator)
│   ├── types.ts                       # Shared interfaces (IWeatherProvider, IWeatherFormatter, etc.)
│   ├── providers/
│   │   ├── base.ts                    # IWeatherProvider interface
│   │   ├── hko.ts                     # HKO provider
│   │   ├── sg_nea.ts                  # Singapore NEA provider
│   │   ├── jma.ts                     # Japan JMA provider
│   │   ├── tw_cwa.ts                  # Taiwan CWA provider
│   │   ├── uk_metoffice.ts            # UK Met Office provider
│   │   ├── au_bom.ts                  # Australia BOM provider
│   │   ├── nz_metservice.ts           # New Zealand MetService provider
│   │   ├── us_nws.ts                  # US NWS provider
│   │   ├── id_bmkg.ts                 # Indonesia BMKG provider
│   │   ├── de_dwd.ts                  # Germany DWD/Bright Sky provider
│   │   ├── kr_kma.ts                  # South Korea KMA provider
│   │   ├── th_tmd.ts                  # Thailand TMD provider
│   │   └── openweathermap.ts          # OpenWeatherMap global fallback
│   ├── formatters/
│   │   ├── base.ts                    # IWeatherFormatter interface
│   │   ├── cli_text.ts                # Plain text output
│   │   ├── telegram.ts                # Telegram MarkdownV2 output
│   │   └── whatsapp.ts                # WhatsApp formatted output
│   └── senders/
│       ├── base.ts                    # IWeatherSender interface + SendResult
│       └── telegram.ts                # Telegram Bot API sender
│
├── tests/                             # Python tests (existing)
├── test/                              # Bun tests (new, mirrors tests/ structure)
│   ├── providers/
│   │   ├── hko.test.ts
│   │   ├── jma.test.ts
│   │   └── ...                        # One test file per provider
│   ├── formatters/
│   │   ├── cli_text.test.ts
│   │   └── telegram.test.ts
│   ├── bootstrap.test.ts
│   └── cli.test.ts
│
├── pyproject.toml                     # Python packaging (unchanged)
├── package.json                       # Bun packaging (new)
├── tsconfig.json                      # TypeScript config (new)
├── bunfig.toml                        # Bun configuration (new, optional)
├── SKILL.md                           # Updated: both Python and Bun integration docs
└── README.md                          # Updated: both install methods
```

### Shared Data Layer

The data that must be extracted from Python source into JSON. Line numbers and counts verified against the working tree on 2026-05-12:

| Source File | Data | Approx Lines | JSON Target |
|-------------|------|-------|-------------|
| `models.py` (~L254-545) | `LOCATION_ALIASES` | ~290 | `data/location-aliases.json` |
| `models.py:37-58` | `CONDITION_EMOJI` | 20 entries | `data/condition-emoji.json` |
| `providers/hko.py:23-45` | `HKO_ICON_MAP` | ~20 | `data/condition-maps/hko-icons.json` |
| `providers/jma.py:28-68` | `JMA_AREA_CODES` | ~40 | `data/cities/jma-area-codes.json` |
| `providers/jma.py:72-181` | `JMA_WEATHER_CODE_MAP` | ~110 (≈100 codes) | `data/condition-maps/jma-codes.json` |
| `providers/us_nws.py` | `US_CITIES` | ~50 | `data/cities/us-nws.json` |
| `providers/us_nws.py` | `NWS_CONDITION_MAP` | ~40 | `data/condition-maps/nws-conditions.json` |
| `providers/sg_nea.py` | `SG_CONDITION_MAP` | ~25 | `data/condition-maps/sg-nea-forecast.json` |
| `providers/de_dwd.py` | `DE_CITIES` | ~30 | `data/cities/de-dwd.json` |
| `providers/de_dwd.py` | `BRIGHTSKY_CONDITION_MAP` | ~15 | `data/condition-maps/brightsky-conditions.json` |
| `providers/openweathermap.py` | `CONDITION_MAP` | ~65 | `data/condition-maps/owm-codes.json` |
| **Subtotal (Phase 1 batch)** | | **~705** | |

> **Phase 1 must also extract the parallel maps from the remaining 7 providers** — CWA (`tw_cwa.py`), Met Office (`uk_metoffice.py`), BOM (`au_bom.py`), MetService (`nz_metservice.py`), BMKG (`id_bmkg.py`), KMA (`kr_kma.py`), TMD (`th_tmd.py`). These contribute the rest of the ~1,300 lines and follow the same pattern. Failing to extract them means Bun providers must duplicate them inline, defeating the shared-data goal.

### Data Packaging (Critical)

The proposed top-level `data/` directory is a **sibling** of the `weather/` Python package, not a child. With the current [`pyproject.toml`](file:///Users/karma/Developer/personal/weather-skill/pyproject.toml) (setuptools, no `package-data` declaration), `pip install weather-skill` will not include `data/` in the wheel, breaking every Python install except editable/dev checkouts.

**Resolution options:**

| Option | Pros | Cons |
|--------|------|------|
| **A. Move data into `weather/data/`** and have Bun read from `weather/data/` (or symlink/copy at build time) | Wheel ships data automatically with `package-data = ["weather/data/*.json", "weather/data/**/*.json"]` | TS package depends on a Python-named directory; aesthetically odd |
| **B. Keep `data/` at root, add to wheel via `[tool.setuptools.package-data]` + a `MANIFEST.in` referencing `../data/*.json`** | Clean repo layout | Setuptools traditionally cannot include files outside the package directory; requires custom build hook or `setuptools-scm`-like dance — fragile |
| **C. Keep `data/` at root, copy into `weather/data/` at build time via a `setuptools` build step** | Clean repo layout, ships in wheel | Adds build complexity; editable installs may go stale |

**Recommendation:** Option A. Use `weather/data/` as the canonical location. Bun loads from `../weather/data/` (or, post-build, the bundler embeds the JSON directly). This keeps Python install behavior unchanged and removes any risk of broken wheels.

If Option A is accepted, update Python loading to use `importlib.resources` rather than `Path(__file__).parent.parent.parent` (which breaks for zipped installs):

```python
# After (hko.py)
from importlib.resources import files
import json

def _load_icon_map() -> dict[str, WeatherCondition]:
    raw = json.loads(
        files("weather.data.condition_maps").joinpath("hko-icons.json").read_text()
    )
    return {k: WeatherCondition(v) for k, v in raw.items()}

HKO_ICON_MAP = _load_icon_map()
```

(Note: `importlib.resources.files()` requires `data/` subdirs to be Python packages — i.e., contain `__init__.py` — or use the `as_file` / `Traversable` API. Decide convention in Phase 1.)

### Python Side: Loading Shared Data

Python providers currently hardcode dicts. After extraction, they load from JSON:

```python
# Before (hko.py)
HKO_ICON_MAP = {
    "pic50.png": WeatherCondition.SUNNY,
    "pic51.png": WeatherCondition.SUNNY,
    ...
}

# After (hko.py)
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

def _load_icon_map() -> dict[str, WeatherCondition]:
    with open(_DATA_DIR / "condition-maps" / "hko-icons.json") as f:
        raw = json.load(f)
    return {k: WeatherCondition(v) for k, v in raw.items()}

HKO_ICON_MAP = _load_icon_map()
```

This is a small refactor to each provider — the logic stays identical, only the data source changes.

### Bun Side: TypeScript Types

Core types mirror the Python dataclasses. **Verified field counts** from [`weather/models.py`](file:///Users/karma/Developer/personal/weather-skill/weather/models.py): `WeatherCondition` has **20** values (not 34 as previously stated), and `WeatherData` has 28+ fields including air-quality and astronomy details.

```typescript
// src/types.ts

enum WeatherCondition {
  Clear = "clear",
  Sunny = "sunny",
  PartlyCloudy = "partly_cloudy",
  Cloudy = "cloudy",
  Overcast = "overcast",
  Fog = "fog",
  Mist = "mist",
  Drizzle = "drizzle",
  Rain = "rain",
  Showers = "showers",
  HeavyRain = "heavy_rain",
  Thunderstorm = "thunderstorm",
  Snow = "snow",
  HeavySnow = "heavy_snow",
  Sleet = "sleet",
  Hail = "hail",
  Windy = "windy",
  Hot = "hot",
  Cold = "cold",
  Unknown = "unknown",
  // 20 values total — must match Python's WeatherCondition exactly
}

// snake_case throughout — matches Python's dataclasses.asdict() output exactly.
// See "JSON Schema Parity" section for rationale.
interface WeatherData {
  // Required
  location: string;
  temperature: number;            // Celsius

  // Location detail
  latitude?: number;
  longitude?: number;

  // Current conditions
  feels_like?: number;
  humidity?: number;              // 0-100
  wind_speed?: number;            // km/h
  wind_direction?: string;
  wind_description?: string;      // Pre-formatted (e.g. "South force 3")
  pressure?: number;              // hPa
  visibility?: number;            // km
  uv_index?: number;

  // Conditions
  condition: WeatherCondition;
  condition_raw?: string;         // Original provider string
  description?: string;

  // Timestamps
  observed_at?: Date;
  fetched_at: Date;               // Default: now()

  // Forecast
  forecast_date?: Date;
  temp_high?: number;
  temp_low?: number;
  precipitation_chance?: number;  // 0-100

  // Air quality
  aqi?: number;                   // US EPA 1-500
  aqhi?: number;                  // HK/Canada 1-10+
  pm25?: number;
  pm10?: number;
  o3?: number;
  no2?: number;

  // Astronomy
  sunrise?: string;
  sunset?: string;

  // Provider metadata
  provider_name: string;
}

interface Location {
  raw: string;
  city?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  normalized: string;
}

interface IWeatherProvider {
  readonly name: string;
  readonly priority: number;
  readonly supportsForecast: boolean;
  supportsLocation(location: Location): boolean;
  getCurrent(location: Location): Promise<WeatherData>;
  getForecast(location: Location, days?: number): Promise<WeatherData[]>;
}

interface IWeatherFormatter {
  readonly platform: string;
  format(data: WeatherData | WeatherData[]): string;
}

interface IWeatherSender {
  readonly channel: string;
  send(message: string, options?: SendOptions): Promise<SendResult>;
}
```

### Bun Side: Provider Pattern

Bun providers are structurally identical to Python but use native `fetch`:

```typescript
// src/providers/hko.ts

const HKO_API_URL = "https://www.hko.gov.hk/wxinfo/json/one_json.xml";

export class HKOProvider implements IWeatherProvider {
  readonly name = "hko";
  readonly priority = 1;
  readonly supportsForecast = true;

  private iconMap: Record<string, WeatherCondition>;

  constructor() {
    // Load from shared data
    this.iconMap = loadConditionMap("hko-icons.json");
  }

  supportsLocation(location: Location): boolean {
    return SUPPORTED_LOCATIONS.has(location.normalized.toLowerCase());
  }

  async getCurrent(location: Location): Promise<WeatherData> {
    const data = await this.fetchApi();
    return this.parseCurrent(data);
  }

  async getForecast(location: Location, days = 3): Promise<WeatherData[]> {
    const data = await this.fetchApi();
    return this.parseForecast(data, days);
  }

  private async fetchApi(): Promise<any> {
    const res = await fetch(HKO_API_URL);
    return res.json();
  }

  // parseCurrent(), parseForecast() — same logic as Python, TS syntax
}
```

### Bun Side: CLI

```typescript
// src/cli.ts

const args = parseArgs(Bun.argv);
const skill = buildDefaultSkill();
// ... same flow as Python cli.py
```

Arg parsing: use a lightweight inline parser (the Python CLI only has 9 flags). No external dependency needed.

### CLI Interface Parity

Both runtimes must accept identical flags and produce identical output. Flags verified against [`weather/cli.py`](file:///Users/karma/Developer/personal/weather-skill/weather/cli.py):

```bash
# These must produce the same output:
python -m weather.cli --location "Hong Kong"
weather --location "Hong Kong"             # console_script entry point
bun run src/cli.ts --location "Hong Kong"
./weather --location "Hong Kong"           # compiled binary

# Flags (9 total — verified):
--location, -l     # Location string (default: "Hong Kong")
--forecast, -f     # Fetch forecast (boolean)
--days, -d         # Forecast days (default: 3; HKO max 9)
--format           # text | telegram | whatsapp | json (default: text)
--send             # Send to configured channel (boolean)
--chat-id          # Override Telegram chat ID
--topic-id         # Telegram topic/thread ID (int)
--provider         # Provider name (default: "auto")
--verbose, -v      # Verbose stderr output

# Edge case parity (Python enforces these — Bun must too):
# - --send + --format json   → exit 2 with stderr error
# - --provider <unknown>     → NoProviderError, list available providers
# - All errors print to stderr; exit code 1 for runtime, 0 for success
```

### JSON Schema Parity (Cross-Runtime)

**Decision: TS uses snake_case throughout** to match Python's `dataclasses.asdict()` output. No transform shim — the in-memory TS model uses the same field names as the on-the-wire JSON.

```typescript
// src/types.ts — snake_case to match Python
interface WeatherData {
  location: string;
  temperature: number;
  feels_like?: number;
  wind_speed?: number;
  wind_description?: string;
  temp_high?: number;
  temp_low?: number;
  precipitation_chance?: number;
  uv_index?: number;
  observed_at?: Date;
  fetched_at: Date;
  forecast_date?: Date;
  provider_name: string;
  // ... all 28+ fields, snake_case
}
```

This is non-idiomatic TypeScript but eliminates an entire category of bugs and removes one moving piece from the cross-runtime parity test. Lint exception: add `// eslint-disable @typescript-eslint/naming-convention` at the top of `src/types.ts`.

**Datetime parity:** Python's CLI currently uses `default=str` which calls `str(datetime)` (space-separated). Switch to `.isoformat()` (T-separated, canonical ISO-8601) on both sides, and **sort keys** to eliminate field-ordering fragility:

```python
# weather/cli.py — Phase 1 change
print(json.dumps(
    output,
    indent=2,
    sort_keys=True,
    default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o),
))
```

```typescript
// src/cli.ts — match (sort keys + ISO-8601)
const sorted = (obj: any): any => {
  if (Array.isArray(obj)) return obj.map(sorted);
  if (obj && typeof obj === "object" && !(obj instanceof Date)) {
    return Object.keys(obj).sort().reduce((acc, k) => { acc[k] = sorted(obj[k]); return acc; }, {} as any);
  }
  return obj;
};
console.log(JSON.stringify(sorted(output), (_k, v) => v instanceof Date ? v.toISOString() : v, 2));
```

A snapshot test diffs Python vs Bun JSON output for fixed mock provider responses — runs on every commit in CI.

### Test Fixtures & Cross-Runtime Parity Test

**Layout** (excluded from wheel and npm distributions):

```
fixtures/
└── api-responses/
    ├── hko/
    │   ├── manifest.json              # URL → file mapping
    │   └── one_json.xml.json          # captured HKO response
    ├── jma/
    │   ├── manifest.json
    │   ├── forecast-130000.json       # Tokyo forecast
    │   └── overview-130000.json       # Tokyo overview
    ├── sg_nea/
    │   ├── manifest.json
    │   └── forecast.json
    ├── us_nws/
    │   ├── manifest.json
    │   ├── points.json
    │   ├── forecast.json
    │   └── observations.json
    └── openweathermap/
        ├── manifest.json
        └── current-london.json
```

**Manifest format** (`fixtures/api-responses/jma/manifest.json`):

```json
{
  "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json": "forecast-130000.json",
  "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/130000.json": "overview-130000.json"
}
```

**Mocking strategy:**
- **Python:** `tests/conftest.py` provides a `mock_http` fixture that monkeypatches `urllib.request.urlopen` to look up the URL in the appropriate manifest and return a `BytesIO` of the canned response.
- **Bun:** `test/setup.ts` uses `mock.module("fetch", ...)` (or `Bun.fetch` patching) to do the same lookup against the same manifest files.

**Clock mocking:**
- Python: `freezegun` (or stdlib `unittest.mock.patch("datetime.datetime")`) → freeze to `2026-01-01T00:00:00+00:00`.
- Bun: `mock.module("Date", ...)` or pass an injected `clock` to providers in tests.

**Capture script** (`scripts/capture-fixtures.sh`, deferred to v0.2):
A simple curl-based tool to refresh fixtures against live APIs when provider responses change. v0.1 captures fixtures manually.

**API key handling in fixtures:**
URLs containing API keys (OWM) are normalized in the manifest using a placeholder (`<API_KEY>`) and the mock layer substitutes before lookup, so real keys never enter version control.

### Compiled Binary

```bash
# Build single binary for NanoClaw Docker
bun build src/cli.ts --compile --outfile weather

# Usage (no Bun runtime needed)
./weather --location "Hong Kong"
```

### SKILL.md Updates

Add Bun integration section alongside existing Python section:

```markdown
## Integration

### Python Agents (OpenClaw, Hermes)

```python
from weather import WeatherSkill
# ... (existing integration unchanged)
```

### Bun/TypeScript Agents (NanoClaw)

```typescript
import { WeatherSkill } from "weather-skill";

const skill = WeatherSkill.fromEnv();
const data = await skill.getCurrent("Hong Kong");
const message = skill.format(data, { platform: "telegram" });
await skill.send(message, { channel: "telegram" });
```

### Agent Execution (CLI)

```bash
# Python runtime
python -m weather.cli --location "<location>"

# Bun runtime
bun run src/cli.ts --location "<location>"

# Compiled binary (no runtime dependency)
./weather --location "<location>"
```

## Success Criteria

### v0.1 (this PRD)

- [ ] `bun run src/cli.ts --location "Hong Kong"` returns HKO data matching Python output
- [ ] `bun run src/cli.ts --location "Tokyo"` returns JMA data
- [ ] `bun run src/cli.ts --location "Singapore"` returns NEA data
- [ ] `bun run src/cli.ts --location "New York"` returns NWS data
- [ ] `bun run src/cli.ts --location "Berlin"` falls through to OpenWeatherMap (or returns "no provider" error if `OPENWEATHERMAP_API_KEY` unset)
- [ ] **Cross-runtime parity**: for the 5 v0.1 providers, `bun run src/cli.ts --format json` and `python -m weather.cli --format json` produce byte-identical JSON when fed identical fixture data
- [ ] `bun run src/cli.ts --location "Hong Kong" --format telegram` produces valid MarkdownV2 matching Python output
- [ ] `bun run src/cli.ts --location "Hong Kong" --format telegram --send` delivers message to Telegram
- [ ] `bun build src/cli.ts --compile --target=bun-linux-x64 --outfile weather && ./weather --location "Hong Kong"` works
- [ ] Compiled binary size < 150MB (NanoClaw Docker constraint, confirm exact ceiling with NanoClaw team)
- [ ] Python package continues to work with zero behavioral changes after data extraction
- [ ] Existing Python test suite passes with data loaded from JSON via `importlib.resources`
- [ ] CI smoke test: `pip wheel . && unzip -l *.whl | grep -c 'weather/data/.*\.json'` returns expected count
- [ ] Bun test suite covers all 5 v0.1 providers, 3 formatters, sender, and CLI
- [ ] SKILL.md documents Python and Bun integration patterns; clearly lists v0.1 (5 providers) vs deferred (8 providers)
- [ ] GitHub release `v0.1.0` ships with `weather-linux-x64` binary attached
- [ ] `weather/data/` is the single source of truth for location aliases, condition maps, and the `WeatherCondition` enum

### PRD-002b (deferred)

- [ ] Bun ports of CWA, Met Office, BOM, MetService, BMKG, DWD, KMA, TMD with parity tests
- [ ] `npm publish @shrwnsan/weather-skill@1.0.0`
- [ ] All 13 providers return data consistent with Python implementations

## Open Questions

1. **Python data loading: lazy vs eager?** Should providers load JSON on first call (lazy) or at import time (eager, like current hardcode)? Eager is simpler and matches current behavior, but means every Python invocation reads 7+ JSON files. For a CLI tool, the I/O overhead is negligible.
   - **Proposed:** Eager at module-import time, gated by a module-level singleton. Matches current semantics, no behavior change.

2. **Formatter utility deduplication.** The Python formatters have duplicated helper methods (`_generate_summary`, `_aqhi_quality`, `_uv_description`) across Telegram and WhatsApp formatters. In Bun, we plan to extract these to `src/utils.ts`. Should we also refactor the Python formatters to use a shared `utils.py`, or accept the asymmetry?
   - **Proposed:** Defer the Python refactor to a separate PRD. This PRD's Goal #6 (zero disruption to Python users) discourages opportunistic refactoring of working code.

3. **Bun version pinning.** Bun is evolving rapidly. What minimum Bun version should we target? Suggest Bun >= 1.1 (stable `fetch`, `build --compile`, `test` runner).
   - **Proposed:** Bun >= 1.1.30 (broad availability + stable `--compile`). Pin in `package.json` `engines` field and CI matrix.

4. **npm publish scope.** Should the Bun package be published to npm eventually? If so, under what name (`weather-skill`, `@claw/weather-skill`, etc.)? Not blocking for v1 but worth deciding early to avoid renames.
   - **Proposed:** Reserve `@shrwnsan/weather-skill` (matches the GitHub owner per [`pyproject.toml`](file:///Users/karma/Developer/personal/weather-skill/pyproject.toml#L20-L23)) immediately, even if publish is deferred. Cheap insurance.

5. **Test data for provider tests.** Provider tests need HTTP mocking. Python tests likely use their own approach. Bun has `bun:test` with built-in mocking. Should test fixture data (mock API responses) also live in `data/` or be duplicated per test suite?
   - **Proposed:** Add a top-level `fixtures/api-responses/<provider>/` (gitignored from packaging) — both runtimes load the same canned JSON files. This is what enables the cross-runtime JSON snapshot test mentioned in *JSON Schema Parity*.

6. **Single source of truth for `WeatherCondition` enum.** Today the enum lives in `weather/models.py`. With shared JSON, the canonical list must live in one place. **Proposed:** add `data/weather-conditions.json` (just the 20 enum string values) and have both `models.py` (Python) and `src/types.ts` (TS) generate/validate against it. A CI check fails if either file drifts.

7. **`python -m weather` vs `python -m weather.cli`.** Currently only `weather.cli` works (no `__main__.py`). **Proposed:** add `weather/__main__.py` that delegates to `cli.cli()` for parity with `bun run src/cli.ts`. One-line file, harmless.

## Phases

### v0.1 Phases (this PRD)

| Phase | Scope | Description |
|-------|-------|-------------|
| **1** | Shared data extraction + packaging | Extract all 13 providers' maps + `LOCATION_ALIASES` + `CONDITION_EMOJI` + `WeatherCondition` enum into JSON. Implement Option A packaging (`weather/data/`). Switch Python loaders to `importlib.resources`. Add CI check that wheel ships JSON files. Switch Python CLI JSON datetime to `.isoformat()`. Verify all existing Python tests pass. |
| **2** | Bun scaffold + core types | `package.json`, `tsconfig.json`, `src/types.ts` (snake_case, 28+ fields), `src/models.ts`, data-loading utility |
| **3** | Bun providers (batch 1) + OWM fallback | HKO, JMA, SG NEA, US NWS, **OpenWeatherMap**. Audit and replicate every Python `urllib.Request` header (esp. `User-Agent` for NWS, JMA). |
| **4** | *(Deferred to PRD-002b)* | — |
| **5** | Bun formatters + sender | cli_text, Telegram (MDV2 escape parity), WhatsApp formatters + Telegram sender + `src/utils.ts` |
| **6** | Bun CLI + bootstrap + binary | `src/cli.ts`, `src/bootstrap.ts`, ISO-8601 datetime serialization, compiled binary build for `bun-linux-x64`, NanoClaw size verification |
| **7** | Bun tests + cross-runtime parity | `bun:test` mirrors Python test structure for the 5 batch-1 providers; add `fixtures/api-responses/` + cross-runtime JSON snapshot diff in CI |
| **8** | Docs + SKILL.md + GitHub release | Update SKILL.md (replace stale NanoClaw Python snippet, mark which providers are v0.1 vs deferred), README, attach compiled binary to GitHub release, tag `v0.1.0` |

### PRD-002b Phases (fast-follow)

| Phase | Scope |
|-------|-------|
| **9** | Bun providers (batch 2): CWA, Met Office, BOM, MetService, BMKG, DWD, KMA, TMD |
| **10** | Tests for batch-2 providers + bump to `v1.0.0` + npm publish |

## Effort Estimate

### v0.1 Effort (this PRD)

> Re-baselined using verified line counts. Assumes one engineer with working Bun + Python familiarity. Provider porting always uncovers small API quirks (timeouts, headers, encoding, date parsing).

| Phase | Hours (low) | Hours (high) | Notes |
|-------|------------:|-------------:|-------|
| 1 — Shared data + packaging | 3 | 5 | Extract **all 13** providers' maps (de-risks PRD-002b), implement Option A packaging, switch Python loaders to `importlib.resources`, ISO-8601 datetime fix, re-run all Python tests |
| 2 — Scaffold + types | 1.5 | 2.5 | `package.json`, `tsconfig.json`, snake_case 28+ field type set, data-loading utility |
| 3 — Providers batch 1 + OWM | 6 | 10 | 5 providers (HKO, JMA, SG NEA, US NWS, OpenWeatherMap) × ~350 LOC + header/UA replication |
| 5 — Formatters + sender | 3 | 5 | cli_text + Telegram MDV2 (escape table) + WhatsApp + Telegram sender + utils |
| 6 — CLI + bootstrap + binary | 2 | 3 | Inline arg parser, env-var-driven bootstrap, ISO-8601 datetime, compiled binary, NanoClaw size verification |
| 7 — Tests + parity | 3 | 5 | 5-provider mocks, formatter snapshots, CLI integration, cross-runtime JSON snapshot diff |
| 8 — Docs + GitHub release | 1 | 1.5 | SKILL.md, README, replace stale NanoClaw section, attach binary to release |
| **v0.1 Total** | **~19.5** | **~32** | Mid-point: ~25h |

### PRD-002b Effort (fast-follow)

| Phase | Hours (low) | Hours (high) | Notes |
|-------|------------:|-------------:|-------|
| 9 — Providers batch 2 | 8 | 13 | 8 remaining providers (CWA, Met Office, BOM, MetService, BMKG, DWD, KMA, TMD); some require API keys for live verification |
| 10 — Tests + npm publish | 3 | 5 | 8-provider mocks, parity tests, npm publish workflow |
| **PRD-002b Total** | **~11** | **~18** | Mid-point: ~14h |

**Combined v0.1 + v1.0:** ~30–50h, but value lands at ~25h instead of ~40h, with production signal between releases to course-correct.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Provider behavior diverges between Python and Bun | Medium | High — different output for same location | Shared data layer + cross-runtime test assertions (Phase 7) |
| Bun `fetch` handles edge cases differently from `urllib` | Medium | Medium — timeout, redirect, encoding differences | Test against live APIs in both runtimes |
| Required HTTP headers missing in Bun port | **Medium** | **High** | NWS rejects requests without a `User-Agent` (and recommends a contact email); JMA already sets `User-Agent: WeatherSkill/1.0` (see [`jma.py:278`](file:///Users/karma/Developer/personal/weather-skill/weather/providers/jma.py#L278)). Audit every Python provider's `urllib.Request` headers and replicate exactly in Bun `fetch` calls. |
| Python wheel stops shipping data files | **Medium** | **High** — every `pip install` breaks | Resolve via Option A in *Data Packaging* section. Add a smoke test: `pip wheel . && unzip -l *.whl \| grep data/.*\.json` in CI. |
| JSON output schema diverges (snake/camel/date format) | **Medium** | Medium — agents that parse JSON break on one runtime | Implement camelCase→snake_case shim in Bun JSON serializer; add cross-runtime snapshot diff test. |
| Shared JSON data drifts out of sync | Low | Medium — one package updated, other broken | CI validates both packages against same data files |
| Bun compiled binary size is too large for NanoClaw Docker | Low | High — defeats the purpose | Bench: Bun compiled binaries are typically ~50-100MB stripped. Verify with NanoClaw team **before** Phase 6. |
| Telegram MarkdownV2 escape rules drift between Python and TS | Low | Medium — rejected messages | Reuse the same escape character set ([`telegram.py:15`](file:///Users/karma/Developer/personal/weather-skill/weather/formatters/telegram.py#L15)) as a constant in shared data, or duplicate with a parity unit test |
| Maintenance burden of two codebases | High | Medium — ongoing cost | Shared data reduces the highest-drift surface. Provider logic is stable and rarely changes. |

## Dependencies

- **Bun >= 1.1** installed in dev environment and CI
- **NanoClaw team confirmation** that a compiled Bun binary (~80-120MB) is acceptable in their Docker image
- **No new Python dependencies** — `json` and `pathlib` are stdlib
