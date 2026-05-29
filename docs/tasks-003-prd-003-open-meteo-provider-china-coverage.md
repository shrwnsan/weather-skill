# Tasks for PRD-003: Open-Meteo Provider + China City Coverage

**PRD:** `docs/prd-003-open-meteo-provider-china-coverage.md`
**Created:** 2026-05-29
**Scope:** Both runtimes — Bun/TypeScript (`src/`) and Python (`weather/`). Shared data files in `weather/data/` serve both.

## Conventions

- ✅ — task complete
- ⏳ — task in progress
- (blank) — not started
- **Parallel: yes** — can be assigned to a separate agent / junior dev alongside other "yes" tasks in the same tier
- **Parallel: no** — gates the next phase; wait for it before starting dependents

## Dependency Graph

```
Tier 0 (all parallel — shared data, no code)
  [1.1 wmo-codes.json]   [1.2 cn.json]   [1.3 location-aliases.json]   [1.4 fixtures]

Tier 1 (parallel with each other; all wait for 1.1 + 1.2)
  ┌─── Bun chain ──────────────────────────────────────────────┐
  │ [2.1 data-loader.ts] → [2.2 open_meteo.ts]                │
  │                         [2.3 bootstrap.ts + index.ts] ←┘  │
  └────────────────────────────────────────────────────────────┘

  ┌─── Python chain ────────────────────────┐
  │ [3.1 open_meteo.py] → [3.2 bootstrap.py] │
  └─────────────────────────────────────────┘

Tier 2 (tests — parallel with each other; wait for Tier 1 + 1.4)
  [4.1 Bun test]   [4.2 Python test]

Tier 3 (docs — wait for Tier 2)
  [5.1 CHANGELOG.md]   [5.2 PRD status update]
```

**Fastest parallel schedule:** 4 agents
- Agent A: Tier 0 (sequential within, small files)
- Agent B: Bun chain (wait for A's 1.1 + 1.2)
- Agent C: Python chain (wait for A's 1.1 + 1.2)
- Agent D: Tier 2 tests (wait for B + C + A's 1.4), then Tier 3 docs

---

## Tier 0 — Shared Data Files

All four tasks are independent. Each touches exactly one file. Assign all in parallel.

---

### Task 1.1 ✅ — Create `weather/data/condition_maps/wmo-codes.json`

**Files:**
- Create: `weather/data/condition_maps/wmo-codes.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

Create the file with the following exact content (WMO 4680 codes as string keys → `WeatherCondition` values):

```json
{
  "0":  "sunny",
  "1":  "sunny",
  "2":  "partly_cloudy",
  "3":  "overcast",
  "45": "fog",
  "48": "fog",
  "51": "drizzle",
  "53": "drizzle",
  "55": "drizzle",
  "56": "drizzle",
  "57": "drizzle",
  "61": "rain",
  "63": "rain",
  "65": "heavy_rain",
  "66": "rain",
  "67": "heavy_rain",
  "71": "snow",
  "73": "snow",
  "75": "heavy_snow",
  "77": "snow",
  "80": "showers",
  "81": "showers",
  "82": "heavy_rain",
  "85": "snow",
  "86": "heavy_snow",
  "95": "thunderstorm",
  "96": "thunderstorm",
  "99": "thunderstorm"
}
```

**Verify:**
```bash
python -c "
import json
d = json.load(open('weather/data/condition_maps/wmo-codes.json'))
assert len(d) == 28
assert d['0'] == 'sunny'
assert d['65'] == 'heavy_rain'
assert d['95'] == 'thunderstorm'
print('wmo-codes.json OK')
"
```

---

### Task 1.2 ✅ — Create `weather/data/cities/cn.json`

**Files:**
- Create: `weather/data/cities/cn.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

Create the file. Include the `"china"` country-level key (→ Beijing) so `--location China` works as a fallback.

```json
{
  "china":     [39.9042, 116.4074],
  "beijing":   [39.9042, 116.4074],
  "shanghai":  [31.2304, 121.4737],
  "guangzhou": [23.1291, 113.2644],
  "shenzhen":  [22.5431, 114.0579],
  "chengdu":   [30.5728, 104.0668],
  "hangzhou":  [30.2741, 120.1551],
  "wuhan":     [30.5928, 114.3055],
  "xian":      [34.3416, 108.9398],
  "nanjing":   [32.0603, 118.7969],
  "chongqing": [29.4316, 106.9123]
}
```

**Verify:**
```bash
python -c "
import json
d = json.load(open('weather/data/cities/cn.json'))
assert len(d) == 11
assert d['shenzhen'] == [22.5431, 114.0579]
assert 'china' in d  # country-level key → Beijing
assert 'xian' in d   # no apostrophe
print('cn.json OK')
"
```

---

### Task 1.3 ✅ — Append Chinese aliases to `weather/data/location-aliases.json`

**Files:**
- Edit: `weather/data/location-aliases.json`

**Depends on:** nothing (but coordinate Task 1.2 must also complete before any provider tests run)
**Parallel:** yes

**Steps:**

Append the following entries to the JSON object **before** the closing `}`. Insert after the last current entry (`"yellowknife": "Yellowknife"`):

```json
  "china":     "China",
  "cn":        "China",
  "中国":       "China",
  "zhongguo":  "China",
  "beijing":   "Beijing",
  "bj":        "Beijing",
  "北京":       "Beijing",
  "shanghai":  "Shanghai",
  "sh":        "Shanghai",
  "上海":       "Shanghai",
  "guangzhou": "Guangzhou",
  "gz":        "Guangzhou",
  "广州":       "Guangzhou",
  "shenzhen":  "Shenzhen",
  "sz":        "Shenzhen",
  "深圳":       "Shenzhen",
  "chengdu":   "Chengdu",
  "成都":       "Chengdu",
  "hangzhou":  "Hangzhou",
  "杭州":       "Hangzhou",
  "wuhan":     "Wuhan",
  "武汉":       "Wuhan",
  "xian":      "Xian",
  "xi'an":     "Xian",
  "西安":       "Xian",
  "nanjing":   "Nanjing",
  "南京":       "Nanjing",
  "chongqing": "Chongqing",
  "重庆":       "Chongqing"
```

> **Conflict check (verified):** `sh`, `cn`, `bj`, `gz`, `sz` are all currently absent from the file. No entries will be overwritten.

**Verify:**
```bash
python -c "
import json
d = json.load(open('weather/data/location-aliases.json'))
assert d.get('sz') == 'Shenzhen'
assert d.get('bj') == 'Beijing'
assert d.get(\"xi'an\") == 'Xian'
assert d.get('cn') == 'China'
assert d.get('sh') == 'Shanghai'
# Ensure existing entries untouched
assert d['hk'] == 'Hong Kong'
assert d['sg'] == 'Singapore'
print('location-aliases.json OK — no conflicts, all CN entries present')
"
```

---

### Task 1.4 ✅ — Create Open-Meteo test fixture

**Files:**
- Create: `fixtures/api-responses/open_meteo/shenzhen-current.json`
- Create: `fixtures/api-responses/open_meteo/manifest.json`

**Depends on:** nothing
**Parallel:** yes

**Steps:**

1. Create `fixtures/api-responses/open_meteo/shenzhen-current.json` with a canned Open-Meteo response for Shenzhen (coordinates 22.5431, 114.0579). The response must include both `current` and `daily` objects so `getCurrent` / `get_current` can extract today's high/low.

   Use this canonical fixture (frozen to 2026-01-01T12:00 UTC):

   ```json
   {
     "latitude": 22.5,
     "longitude": 114.0625,
     "generationtime_ms": 0.25,
     "utc_offset_seconds": 0,
     "timezone": "GMT",
     "timezone_abbreviation": "GMT",
     "elevation": 8.0,
     "current_units": {
       "time": "iso8601",
       "interval": "seconds",
       "temperature_2m": "°C",
       "relative_humidity_2m": "%",
       "weather_code": "wmo code",
       "wind_speed_10m": "km/h",
       "apparent_temperature": "°C"
     },
     "current": {
       "time": "2026-01-01T12:00",
       "interval": 900,
       "temperature_2m": 18.4,
       "relative_humidity_2m": 72,
       "weather_code": 2,
       "wind_speed_10m": 11.2,
       "apparent_temperature": 17.1
     },
     "daily_units": {
       "time": "iso8601",
       "weather_code": "wmo code",
       "temperature_2m_max": "°C",
       "temperature_2m_min": "°C",
       "precipitation_probability_max": "%",
       "sunrise": "iso8601",
       "sunset": "iso8601"
     },
     "daily": {
       "time": ["2026-01-01"],
       "weather_code": [2],
       "temperature_2m_max": [22.1],
       "temperature_2m_min": [14.3],
       "precipitation_probability_max": [10],
       "sunrise": ["2026-01-01T06:52"],
       "sunset": ["2026-01-01T17:58"]
     }
   }
   ```

2. Create `fixtures/api-responses/open_meteo/manifest.json` using the **`urls` object format** (not `responses` array) to match the `loadFixtures()` logic in `test/setup.ts` (line 64: `Object.entries(manifest.urls)`) and `_load_manifests()` in `tests/conftest.py` (line 35: `manifest.get("urls", {}).items()`):

   ```json
   {
     "urls": {
       "https://api.open-meteo.com/v1/forecast?latitude=22.5431&longitude=114.0579&current=temperature_2m%2Crelative_humidity_2m%2Cweather_code%2Cwind_speed_10m%2Capparent_temperature&daily=weather_code%2Ctemperature_2m_max%2Ctemperature_2m_min%2Cprecipitation_probability_max%2Csunrise%2Csunset&forecast_days=1&timezone=UTC": "shenzhen-current.json"
     }
   }
   ```

   > **URL encoding note:** `URLSearchParams` percent-encodes commas in parameter values. The manifest key must match the URL string as constructed by the provider's `buildUrl()` / `urllib.parse.urlencode()`. Verify the exact URL by running the provider once in verbose mode or by inspecting the fetch mock 404 log.

3. Update `test/setup.ts` — add `"open_meteo"` to the `PROVIDERS` constant (line 29). Without this, `loadFixtures()` skips the `fixtures/api-responses/open_meteo/` directory entirely:

   ```typescript
   const PROVIDERS = [
     "hko",
     "jma",
     "sg_nea",
     "us_nws",
     "openweathermap",
     "de_dwd",
     "nz_metservice",
     "id_bmkg",
     "au_bom",
     "kr_kma",
     "th_tmd",
     "uk_metoffice",
     "tw_cwa",
     "open_meteo",  // ← add
   ] as const;
   ```

4. Update `tests/conftest.py` — add `"open_meteo"` to `_PROVIDERS` (line 21). Without this, the `mock_http` fixture does not load Open-Meteo fixtures, causing `FileNotFoundError` in every Python test:

   ```python
   _PROVIDERS = ("hko", "jma", "sg_nea", "us_nws", "openweathermap", "open_meteo")
   ```

**Verify:**
```bash
python -c "
import json
r = json.load(open('fixtures/api-responses/open_meteo/shenzhen-current.json'))
assert r['current']['temperature_2m'] == 18.4
assert r['current']['weather_code'] == 2
assert r['daily']['temperature_2m_max'] == [22.1]
m = json.load(open('fixtures/api-responses/open_meteo/manifest.json'))
assert 'urls' in m, 'must use urls object, not responses array'
assert len(m['urls']) == 1
print('Open-Meteo fixtures OK')
"

---

## Tier 1A — Bun Runtime

Run after Tasks 1.1 and 1.2 complete. Tasks 2.1 → 2.2 → 2.3 are sequential within this chain.

---

### Task 2.1 ✅ — Update `src/data-loader.ts`

**Files:**
- Edit: `src/data-loader.ts`

**Depends on:** 1.1 (wmo-codes.json), 1.2 (cn.json)
**Parallel:** yes (with Tier 1B Python chain)

**Steps:**

1. Add two new JSON imports after the existing city imports (after `metofficeCitiesRaw`):

   ```typescript
   import cnCitiesRaw from "../weather/data/cities/cn.json" with { type: "json" };
   ```

   Add one more for the WMO codes, after the `tmdConditionsRaw` import:

   ```typescript
   import wmoCodesRaw from "../weather/data/condition_maps/wmo-codes.json" with { type: "json" };
   ```

2. Add two new exports in the "City lookups" section (after `METOFFICE_CITIES`):

   ```typescript
   export const CN_CITIES: Record<string, [number, number]> =
     cnCitiesRaw as unknown as Record<string, [number, number]>;
   ```

3. Add one new export in the "Condition maps" section (after `TMD_CONDITION_MAP`):

   ```typescript
   export const WMO_CODE_MAP: Record<string, WeatherCondition> =
     buildConditionMap(wmoCodesRaw as Record<string, string>);
   ```

**Verify:**
```bash
bun run typecheck
# Expect: 0 errors
bun -e "import { CN_CITIES, WMO_CODE_MAP } from './src/data-loader.js'; console.log(CN_CITIES['shenzhen'], WMO_CODE_MAP['0'])"
# Expect: [ 22.5431, 114.0579 ] sunny
```

---

### Task 2.2 ✅ — Create `src/providers/open_meteo.ts`

**Files:**
- Create: `src/providers/open_meteo.ts`

**Depends on:** 2.1
**Parallel:** no (within Bun chain)

**Steps:**

Create the file. Key contracts:
- `name = "open-meteo"`, `priority = 11`, `requiresApiKey = false`, `supportsForecast = true`
- `supportsLocation` calls private `resolveCoords` → checks `CN_CITIES`, `US_NWS_CITIES`, `DE_DWD_CITIES`, `METOFFICE_CITIES` (in that order)
- `getCurrent` fetches with both `current=` and `daily=` params → parses `response.current` + `response.daily[0]` for today's high/low
- `getForecast` fetches with `daily=` only + `forecast_days=N` → maps each `daily.time[i]` to a `WeatherData`
- Display name: `titleCase(location.normalized)` (Open-Meteo does not return a city name)
- HTTP error handling mirrors `openweathermap.ts` — catch fetch errors → `ProviderError`

Full implementation template:

```typescript
/* eslint-disable @typescript-eslint/naming-convention */
/**
 * Open-Meteo provider — zero-config global fallback.
 *
 * Free, no API key. Endpoint: api.open-meteo.com/v1/forecast
 * Requires lat/lon; resolves from the merged city lookup tables.
 * Priority 11 — lowest in the chain, activates when every higher-priority
 * provider has declined or failed.
 */

import {
  CN_CITIES,
  DE_DWD_CITIES,
  METOFFICE_CITIES,
  US_NWS_CITIES,
  WMO_CODE_MAP,
} from "../data-loader.js";
import { makeWeatherData } from "../models.js";
import {
  type IWeatherProvider,
  type Location,
  LocationNotSupportedError,
  ProviderError,
  WeatherCondition,
  type WeatherData,
} from "../types.js";

const BASE_URL = "https://api.open-meteo.com/v1/forecast";

const CURRENT_PARAMS =
  "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature";
const DAILY_PARAMS =
  "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset";

export class OpenMeteoProvider implements IWeatherProvider {
  readonly name = "open-meteo";
  readonly priority = 11;
  readonly supportsForecast = true;
  readonly requiresApiKey = false;

  supportsLocation(location: Location): boolean {
    return this.resolveCoords(location) !== null;
  }

  async getCurrent(location: Location): Promise<WeatherData> {
    const coords = this.resolveCoords(location);
    if (!coords) {
      throw new LocationNotSupportedError(
        `Open-Meteo: cannot resolve coordinates for: ${location.raw}`,
      );
    }
    const [lat, lon] = coords;
    const url = this.buildUrl(lat, lon, {
      current: CURRENT_PARAMS,
      daily: DAILY_PARAMS,
      forecast_days: "1",
      timezone: "UTC",
    });
    const data = await this.fetchJson(url);
    return this.parseCurrent(location, data);
  }

  async getForecast(location: Location, days: number = 7): Promise<WeatherData[]> {
    const coords = this.resolveCoords(location);
    if (!coords) {
      throw new LocationNotSupportedError(
        `Open-Meteo: cannot resolve coordinates for: ${location.raw}`,
      );
    }
    const [lat, lon] = coords;
    const url = this.buildUrl(lat, lon, {
      daily: DAILY_PARAMS,
      forecast_days: String(Math.min(days, 16)),
      timezone: "UTC",
    });
    const data = await this.fetchJson(url);
    return this.parseForecast(location, data, days);
  }

  // ── Private helpers ───────────────────────────────────────────────

  private resolveCoords(location: Location): [number, number] | null {
    if (location.latitude != null && location.longitude != null) {
      return [location.latitude, location.longitude];
    }
    const n = location.normalized;
    return (
      CN_CITIES[n] ??
      US_NWS_CITIES[n] ??
      DE_DWD_CITIES[n] ??
      METOFFICE_CITIES[n] ??
      null
    );
  }

  private buildUrl(
    lat: number,
    lon: number,
    extra: Record<string, string>,
  ): string {
    const params = new URLSearchParams({
      latitude: lat.toFixed(4),
      longitude: lon.toFixed(4),
      ...extra,
    });
    return `${BASE_URL}?${params.toString()}`;
  }

  private async fetchJson(url: string): Promise<Record<string, any>> {
    let res: Response;
    try {
      res = await fetch(url);
    } catch (e) {
      throw new ProviderError(
        `Open-Meteo request failed: ${(e as Error).message}`,
      );
    }
    if (!res.ok) {
      throw new ProviderError(`Open-Meteo API error: HTTP ${res.status}`);
    }
    return (await res.json()) as Record<string, any>;
  }

  private parseCurrent(
    location: Location,
    data: Record<string, any>,
  ): WeatherData {
    const current = (data.current ?? {}) as Record<string, any>;
    const daily = (data.daily ?? {}) as Record<string, any>;

    const wmoCode = current.weather_code ?? 0;
    const condition = WMO_CODE_MAP[String(wmoCode)] ?? WeatherCondition.Unknown;

    const tempHigh =
      Array.isArray(daily.temperature_2m_max) &&
      typeof daily.temperature_2m_max[0] === "number"
        ? daily.temperature_2m_max[0]
        : undefined;
    const tempLow =
      Array.isArray(daily.temperature_2m_min) &&
      typeof daily.temperature_2m_min[0] === "number"
        ? daily.temperature_2m_min[0]
        : undefined;

    const windSpeedKmh =
      typeof current.wind_speed_10m === "number"
        ? current.wind_speed_10m
        : undefined;

    const precipChance =
      Array.isArray(daily.precipitation_probability_max) &&
      typeof daily.precipitation_probability_max[0] === "number"
        ? daily.precipitation_probability_max[0]
        : undefined;

    const sunrise =
      Array.isArray(daily.sunrise) && typeof daily.sunrise[0] === "string"
        ? daily.sunrise[0]
        : undefined;
    const sunset =
      Array.isArray(daily.sunset) && typeof daily.sunset[0] === "string"
        ? daily.sunset[0]
        : undefined;

    return makeWeatherData({
      location: titleCase(location.normalized),
      temperature:
        typeof current.temperature_2m === "number"
          ? current.temperature_2m
          : 0,
      condition,
      condition_raw: `wmo:${wmoCode}`,
      provider_name: this.name,
      observed_at: typeof current.time === "string"
        ? new Date(String(current.time))
        : new Date(),
      latitude: typeof data.latitude === "number" ? data.latitude : undefined,
      longitude:
        typeof data.longitude === "number" ? data.longitude : undefined,
      ...(typeof current.relative_humidity_2m === "number"
        ? { humidity: current.relative_humidity_2m }
        : {}),
      ...(typeof current.apparent_temperature === "number"
        ? { feels_like: current.apparent_temperature }
        : {}),
      ...(windSpeedKmh != null ? { wind_speed: windSpeedKmh } : {}),
      ...(tempHigh != null ? { temp_high: tempHigh } : {}),
      ...(tempLow != null ? { temp_low: tempLow } : {}),
      ...(precipChance != null ? { precipitation_chance: precipChance } : {}),
      ...(sunrise ? { sunrise } : {}),
      ...(sunset ? { sunset } : {}),
    });
  }

  private parseForecast(
    location: Location,
    data: Record<string, any>,
    days: number,
  ): WeatherData[] {
    const daily = (data.daily ?? {}) as Record<string, any>;
    const times: string[] = Array.isArray(daily.time) ? daily.time : [];
    const wmoCodes: number[] = Array.isArray(daily.weather_code)
      ? daily.weather_code
      : [];
    const maxTemps: number[] = Array.isArray(daily.temperature_2m_max)
      ? daily.temperature_2m_max
      : [];
    const minTemps: number[] = Array.isArray(daily.temperature_2m_min)
      ? daily.temperature_2m_min
      : [];
    const precipChances: number[] = Array.isArray(
      daily.precipitation_probability_max,
    )
      ? daily.precipitation_probability_max
      : [];
    const sunrises: string[] = Array.isArray(daily.sunrise)
      ? daily.sunrise
      : [];
    const sunsets: string[] = Array.isArray(daily.sunset) ? daily.sunset : [];

    const locationName = titleCase(location.normalized);

    return times.slice(0, days).map((dateStr, i) => {
      const wmoCode = wmoCodes[i] ?? 0;
      const condition =
        WMO_CODE_MAP[String(wmoCode)] ?? WeatherCondition.Unknown;

      return makeWeatherData({
        location: locationName,
        temperature: 0,
        condition,
        condition_raw: `wmo:${wmoCode}`,
        provider_name: this.name,
        forecast_date: new Date(`${dateStr}T00:00:00.000Z`),
        ...(typeof maxTemps[i] === "number" ? { temp_high: maxTemps[i] } : {}),
        ...(typeof minTemps[i] === "number" ? { temp_low: minTemps[i] } : {}),
        ...(typeof precipChances[i] === "number"
          ? { precipitation_chance: precipChances[i] }
          : {}),
        ...(typeof sunrises[i] === "string" ? { sunrise: sunrises[i] } : {}),
        ...(typeof sunsets[i] === "string" ? { sunset: sunsets[i] } : {}),
      });
    });
  }
}

// ── Helpers ────────────────────────────────────────────────────────

function titleCase(s: string): string {
  return s
    .split(/[\s_-]+/)
    .map((w) => (w ? w[0]!.toUpperCase() + w.slice(1) : w))
    .join(" ");
}
```

**Verify:**
```bash
bun run typecheck
# Expect: 0 errors
```

---

### Task 2.3 ✅ — Update `src/bootstrap.ts` and `src/index.ts`

**Files:**
- Edit: `src/bootstrap.ts`
- Edit: `src/index.ts`

**Depends on:** 2.2
**Parallel:** no

**Steps:**

**`src/bootstrap.ts`:**
1. Add import after `OpenWeatherMapProvider` import:
   ```typescript
   import { OpenMeteoProvider } from "./providers/open_meteo.js";
   ```
2. In `buildProviders()`, append **after** the `cwaKey` block:
   ```typescript
   // Free zero-config global fallback — always registered.
   providers.push(new OpenMeteoProvider());
   ```

**`src/index.ts`:**
1. Add export after the `CWAProvider` export line:
   ```typescript
   export { OpenMeteoProvider } from "./providers/open_meteo.js";
   ```

**Verify:**
```bash
bun run typecheck
# Expect: 0 errors
bun -e "
import { buildDefaultSkill } from './src/bootstrap.js';
const s = buildDefaultSkill();
const p = s.providers.find(p => p.name === 'open-meteo');
console.assert(p != null, 'open-meteo provider not registered');
console.assert(p.priority === 11, 'wrong priority');
console.log('bootstrap OK — open-meteo registered at priority', p.priority);
"
```

---

## Tier 1B — Python Runtime

Run after Tasks 1.1 and 1.2 complete. Runs in **parallel with Tier 1A**. Tasks 3.1 → 3.2 are sequential within this chain.

---

### Task 3.1 ✅ — Create `weather/providers/open_meteo.py`

**Files:**
- Create: `weather/providers/open_meteo.py`

**Depends on:** 1.1, 1.2
**Parallel:** yes (with Tier 1A)

**Reference:** Mirror `weather/providers/openweathermap.py` and `weather/providers/de_dwd.py` for structure and HTTP/async patterns.

**Steps:**

Create the file. Key contracts:
- Class `OpenMeteoProvider(WeatherProvider)` with `priority = 11`, `name = "open-meteo"`, `supports_forecast = True`, `requires_api_key = False`
- `supports_location` calls `_resolve_coords` — returns `True` if not `None`
- `_resolve_coords` merges CN_CITIES + US_NWS_CITIES + DE_CITIES + METOFFICE_CITIES (all loaded via `load_json`)
- `get_current` and `get_forecast` use `asyncio.get_running_loop().run_in_executor(None, fetch)` + `urllib.request.urlopen` exactly like `de_dwd.py`
- Display name: `location.normalized.title()` (Python equivalent of `titleCase`)

```python
"""
Open-Meteo provider — zero-config global fallback.

Free, no API key. Endpoint: api.open-meteo.com/v1/forecast
Requires lat/lon; resolves from the merged city lookup tables.
Priority 11 — lowest in the chain.
"""

import asyncio
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from typing import Optional

from ..data.loader import load_json
from ..models import Location, WeatherCondition, WeatherData
from .base import LocationNotSupportedError, ProviderError, WeatherProvider

# Load city coordinate tables — shared with Bun runtime.
_CN_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "cn.json").items()
}
_US_NWS_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "us-nws.json").items()
}
_DE_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "de-dwd.json").items()
}
_METOFFICE_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "metoffice.json").items()
}

_WMO_CODE_MAP: dict[int, WeatherCondition] = {
    int(k): WeatherCondition(v)
    for k, v in load_json("condition_maps", "wmo-codes.json").items()
}

_BASE_URL = "https://api.open-meteo.com/v1/forecast"
_CURRENT_PARAMS = (
    "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature"
)
_DAILY_PARAMS = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max,sunrise,sunset"
)


class OpenMeteoProvider(WeatherProvider):
    """
    Open-Meteo weather provider.

    Coverage: Global (via lat/lon lookup)
    API Key: None required
    Priority: 11 (zero-config catch-all fallback below OpenWeatherMap)
    """

    priority = 11
    supports_forecast = True
    supports_air_quality = False
    requires_api_key = False

    @property
    def name(self) -> str:
        return "open-meteo"

    def supports_location(self, location: Location) -> bool:
        return self._resolve_coords(location) is not None

    async def get_current(self, location: Location) -> WeatherData:
        coords = self._resolve_coords(location)
        if coords is None:
            raise LocationNotSupportedError(
                f"Open-Meteo: cannot resolve coordinates for: {location.raw}"
            )
        lat, lon = coords
        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "current": _CURRENT_PARAMS,
            "daily": _DAILY_PARAMS,
            "forecast_days": "1",
            "timezone": "UTC",
        }
        data = await self._fetch(params)
        return self._parse_current(location, data)

    async def get_forecast(
        self, location: Location, days: int = 7
    ) -> list[WeatherData]:
        coords = self._resolve_coords(location)
        if coords is None:
            raise LocationNotSupportedError(
                f"Open-Meteo: cannot resolve coordinates for: {location.raw}"
            )
        lat, lon = coords
        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "daily": _DAILY_PARAMS,
            "forecast_days": str(min(days, 16)),
            "timezone": "UTC",
        }
        data = await self._fetch(params)
        return self._parse_forecast(location, data, days)

    # ── Private helpers ────────────────────────────────────────────────

    def _resolve_coords(
        self, location: Location
    ) -> Optional[tuple[float, float]]:
        if location.latitude is not None and location.longitude is not None:
            return (location.latitude, location.longitude)
        n = location.normalized
        return (
            _CN_CITIES.get(n)
            or _US_NWS_CITIES.get(n)
            or _DE_CITIES.get(n)
            or _METOFFICE_CITIES.get(n)
        )

    async def _fetch(self, params: dict) -> dict:
        url = f"{_BASE_URL}?{urllib.parse.urlencode(params)}"
        loop = asyncio.get_running_loop()

        def fetch():
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                raise ProviderError(f"Open-Meteo API error: HTTP {e.code}")
            except Exception as e:
                raise ProviderError(f"Open-Meteo request failed: {e}")

        return await loop.run_in_executor(None, fetch)

    def _parse_current(self, location: Location, data: dict) -> WeatherData:
        current = data.get("current", {})
        daily = data.get("daily", {})

        wmo_code = current.get("weather_code", 0)
        condition = _WMO_CODE_MAP.get(wmo_code, WeatherCondition.UNKNOWN)

        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip_chances = daily.get("precipitation_probability_max", [])
        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])

        return WeatherData(
            location=location.normalized.title(),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            temperature=current.get("temperature_2m", 0.0),
            feels_like=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            wind_speed=current.get("wind_speed_10m"),
            temp_high=max_temps[0] if max_temps else None,
            temp_low=min_temps[0] if min_temps else None,
            precipitation_chance=precip_chances[0] if precip_chances else None,
            sunrise=sunrises[0] if sunrises else None,
            sunset=sunsets[0] if sunsets else None,
            condition=condition,
            condition_raw=f"wmo:{wmo_code}",
            observed_at=datetime.now(timezone.utc),
            provider_name=self.name,
        )

    def _parse_forecast(
        self, location: Location, data: dict, days: int
    ) -> list[WeatherData]:
        daily = data.get("daily", {})
        times: list[str] = daily.get("time", [])
        wmo_codes: list[int] = daily.get("weather_code", [])
        max_temps: list[float] = daily.get("temperature_2m_max", [])
        min_temps: list[float] = daily.get("temperature_2m_min", [])
        precip_chances: list[int] = daily.get("precipitation_probability_max", [])
        sunrises: list[str] = daily.get("sunrise", [])
        sunsets: list[str] = daily.get("sunset", [])

        location_name = location.normalized.title()
        forecasts = []

        for i, date_str in enumerate(times[:days]):
            wmo_code = wmo_codes[i] if i < len(wmo_codes) else 0
            condition = _WMO_CODE_MAP.get(wmo_code, WeatherCondition.UNKNOWN)
            forecasts.append(
                WeatherData(
                    location=location_name,
                    temperature=0.0,
                    condition=condition,
                    condition_raw=f"wmo:{wmo_code}",
                    forecast_date=date.fromisoformat(date_str),
                    temp_high=max_temps[i] if i < len(max_temps) else None,
                    temp_low=min_temps[i] if i < len(min_temps) else None,
                    precipitation_chance=(
                        precip_chances[i] if i < len(precip_chances) else None
                    ),
                    sunrise=sunrises[i] if i < len(sunrises) else None,
                    sunset=sunsets[i] if i < len(sunsets) else None,
                    provider_name=self.name,
                )
            )
        return forecasts
```

> **Validation note (T-4):** `_WMO_CODE_MAP` is built with `WeatherCondition(v)` which raises `ValueError` at module import time if a value in `wmo-codes.json` is not a valid enum member. This is intentional fail-fast behaviour — a typo in the JSON will surface immediately rather than silently mapping to `UNKNOWN`. No change needed.

**Verify:**
```bash
python -c "
from weather.providers.open_meteo import OpenMeteoProvider
from weather.models import Location
p = OpenMeteoProvider()
assert p.priority == 11
assert p.name == 'open-meteo'
sz = Location(raw='Shenzhen', normalized='shenzhen')
assert p.supports_location(sz), 'shenzhen should be supported'
unknown = Location(raw='Atlantis', normalized='atlantis')
assert not p.supports_location(unknown), 'atlantis should not be supported'
print('open_meteo.py import + supports_location OK')
"

---

### Task 3.2 ✅ — Update `weather/bootstrap.py`

**Files:**
- Edit: `weather/bootstrap.py`

**Depends on:** 3.1
**Parallel:** no (within Python chain)

**Steps:**

In `_build_providers()`, append **after** the `owm_key` block (last existing conditional):

```python
    # Free zero-config global fallback — always registered.
    from .providers.open_meteo import OpenMeteoProvider
    providers.append(OpenMeteoProvider())
```

Also update `weather/providers/__init__.py` (T-5):
1. Add to the module docstring (after the `OpenWeatherMapProvider` line):
   ```
   - OpenMeteoProvider: Zero-config global fallback (priority 11, free, no API key)
   ```
2. Add import: `from .open_meteo import OpenMeteoProvider`
3. Add `"OpenMeteoProvider"` to `__all__`

**Verify:**
```bash
python -c "
from weather.bootstrap import build_default_skill
skill = build_default_skill()
names = [p.name for p in skill.providers]
assert 'open-meteo' in names, f'open-meteo missing: {names}'
om = next(p for p in skill.providers if p.name == 'open-meteo')
assert om.priority == 11
# Must be last in priority order
priorities = sorted(p.priority for p in skill.providers)
assert priorities[-1] == 11
print('bootstrap OK — open-meteo at priority', om.priority)
"
```

---

## Tier 2 — Tests

Both test tasks are independent. Run in parallel after Tier 1A+1B and Task 1.4 complete.

---

### Task 4.1 ✅ — Bun provider test

**Files:**
- Create: `test/providers/open_meteo.test.ts`

**Depends on:** 2.2, 2.3, 1.4
**Parallel:** yes (with 4.2)

**Reference:** `test/providers/us_nws.test.ts` and `test/providers/hko.test.ts` for test structure and fixture replay.

**Steps:**

Create `test/providers/open_meteo.test.ts` with:

1. **Import** `OpenMeteoProvider` and fixture URL helpers
2. **`supportsLocation` suite** (no network needed):
   - Returns `true` for `"shenzhen"` (in CN_CITIES)
   - Returns `true` for `"new york"` (in US_NWS_CITIES)
   - Returns `true` for `"berlin"` (in DE_DWD_CITIES)
   - Returns `false` for `"atlantis"` (in no city database)
3. **`getCurrent` suite** (uses `mockFetch` from `test/setup.ts`):
   - Parses Shenzhen fixture: `temperature ≈ 18.4`, `condition = WeatherCondition.PartlyCloudy` (wmo code 2), `humidity = 72`, `feels_like = 17.1`, `temp_high = 22.1`, `temp_low = 14.3`
   - `provider_name === "open-meteo"`
   - `location === "Shenzhen"` (titleCase of "shenzhen")
4. **Alias test**: `parseLocation("sz")` → `normalized = "shenzhen"` → `supportsLocation` returns `true`

**Verify:**
```bash
bun test test/providers/open_meteo.test.ts
# Expect: all tests pass, 0 failures
bun test
# Expect: all existing tests still pass (no regressions)
bun run typecheck
```

---

### Task 4.2 ✅ — Python provider test

**Files:**
- Create: `tests/test_open_meteo.py`

**Depends on:** 3.1, 3.2, 1.4
**Parallel:** yes (with 4.1)

**Reference:** `tests/test_openweathermap.py` or any existing provider test for mock_http fixture pattern.

**Steps:**

Create `tests/test_open_meteo.py` with `pytest` tests:

1. **`test_supports_location_chinese_city`** — `OpenMeteoProvider().supports_location(Location(raw="Shenzhen", normalized="shenzhen"))` returns `True`
2. **`test_supports_location_unknown`** — `Location(raw="Atlantis", normalized="atlantis")` returns `False`
3. **`test_supports_location_country_key`** — `Location(raw="China", normalized="china")` returns `True` (country-level key in cn.json)
4. **`test_get_current_shenzhen`** (uses `mock_http` fixture from `tests/conftest.py`):
   - `weather = await OpenMeteoProvider().get_current(Location(raw="Shenzhen", normalized="shenzhen"))`
   - Assert `weather.temperature == 18.4`
   - Assert `weather.condition == WeatherCondition.PARTLY_CLOUDY` (wmo 2)
   - Assert `weather.humidity == 72`
   - Assert `weather.feels_like == 17.1`
   - Assert `weather.temp_high == 22.1`
   - Assert `weather.temp_low == 14.3`
   - Assert `weather.provider_name == "open-meteo"`
5. **`test_alias_resolution`** — using `weather.models.parse_location("sz")` produces `normalized = "shenzhen"` and provider returns `True` for `supports_location`

**Verify:**
```bash
pytest tests/test_open_meteo.py -v
# Expect: all tests pass
pytest
# Expect: no regressions in full test suite
```

---

## Tier 3 — Docs

Run sequentially after Tier 2 passes.

---

### Task 5.1 ✅ — Update `CHANGELOG.md`

**Files:**
- Edit: `CHANGELOG.md`

**Depends on:** 4.1, 4.2
**Parallel:** yes (with 5.2)

**Steps:**

In the `[Unreleased]` section, append to (or create) the `### Added` block:

```markdown
- **Open-Meteo provider** (`open-meteo`, priority 11) — zero-config global fallback below
  OpenWeatherMap. Free, no API key required. Resolves coordinates from the merged city
  lookup (`cn.json`, `us-nws.json`, `de-dwd.json`, `metoffice.json`). Backed by
  ECMWF/GFS models via `api.open-meteo.com/v1/forecast`. Activates only when all
  higher-priority providers have declined or failed (priority 10 = OWM). Implemented in
  both Bun (`src/providers/open_meteo.ts`) and Python (`weather/providers/open_meteo.py`).
  Registered unconditionally in `buildDefaultSkill()` / `build_default_skill()`. Provider
  count: 13 → 14.
- **`weather/data/cities/cn.json`** — coordinates for 10 major Chinese cities (Beijing,
  Shanghai, Guangzhou, Shenzhen, Chengdu, Hangzhou, Wuhan, Xi'an, Nanjing, Chongqing)
  plus a `"china"` country-level key (→ Beijing). Both runtimes read this file.
- **Chinese city aliases** — 29 new entries in `weather/data/location-aliases.json`
  covering Latin (`sz`, `gz`, `sh`, `bj`, `cn`, full city names), CJK script (e.g. `深圳`,
  `北京`, `中国`), and romanisation variants (`xi'an`). Running `--location sz` now
  resolves to Shenzhen via Open-Meteo.
- **`weather/data/condition_maps/wmo-codes.json`** — WMO 4680 weather code → `WeatherCondition`
  mapping (28 codes, shared by both runtimes).
```

---

### Task 5.2 ✅ — Update PRD status

**Files:**
- Edit: `docs/prd-003-open-meteo-provider-china-coverage.md`

**Depends on:** 4.1, 4.2
**Parallel:** yes (with 5.1)

**Steps:**

Change the status line from `Draft` to `Complete` and add a completion note:

```markdown
**Status:** Complete
**Completed:** <date>
```
