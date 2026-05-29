# PRD-003: Open-Meteo Provider + China City Coverage

**Status:** Draft
**Created:** 2026-05-29
**Priority:** High
**GitHub Issue:** [#39](https://github.com/shrwnsan/weather-skill/issues/39)

## Problem Statement

Running `bun run src/cli.ts --location "Shenzhen" --format telegram` returns:

```
Error: No provider supports location: Shenzhen
```

China's major cities have no dedicated provider and no coordinates in any existing city data file. More broadly, **any location not covered by a dedicated regional provider and without an `OPENWEATHERMAP_API_KEY` configured will fail entirely**, even though free, zero-config global weather data is available via Open-Meteo.

### Root Cause

Two independent gaps:

1. **No Open-Meteo provider.** Open-Meteo (`api.open-meteo.com/v1/forecast`) is a free, no-key-needed API with global coverage backed by ECMWF/GFS models. It is the natural zero-config safety net that belongs below OpenWeatherMap in the provider chain.

2. **No Chinese city coordinate data.** `weather/data/cities/` contains files for JMA (Japan), NWS (USA), DWD (Germany), and Met Office (UK) — but nothing for China. `location-aliases.json` has no Chinese city entries either.

### Current Provider Chain Gap

```
Priority 1–9   HKO, SG NEA, JMA, CWA, Met Office, BOM, MetService, NWS, DWD, BMKG, KMA, TMD
Priority 10    OpenWeatherMap  ← key required; absent when OPENWEATHERMAP_API_KEY unset
Priority 11    (gap) ← zero-config requests for unlisted cities fail here
```

Any user without `OPENWEATHERMAP_API_KEY` and querying a non-dedicated-provider city gets an error.

## Open-Meteo vs OpenWeatherMap

They are complementary, not competing:

| | OpenWeatherMap | Open-Meteo |
|---|---|---|
| API key | Required (free tier: 1 000 calls/day) | None — zero config |
| Priority | 10 | 11 (proposed, lowest) |
| Data source | OWM synthesis | ECMWF / GFS models |
| Coverage | Global via city-name query | Global via lat/lon |
| Rich fields | Air quality, alerts, historical | 16-day forecast, WMO codes, sunrise/sunset |

Value proposition of adding Open-Meteo:

| Scenario | Without | With |
|---|---|---|
| Has OWM key | OWM handles it (priority 10) | No change |
| No OWM key, unrecognised city | Error | Open-Meteo catches it (priority 11) |
| OWM rate-limited / down | Error | Open-Meteo fallback |

## Goals

1. **Add `OpenMeteoProvider`** at priority 11 — the catch-all free fallback below OWM.
2. **Add `weather/data/cities/cn.json`** with coordinates for 10 major Chinese cities.
3. **Add Chinese aliases** to `weather/data/location-aliases.json`.
4. **Register Open-Meteo unconditionally** in `buildDefaultSkill()` (no key required).
5. **Export `OpenMeteoProvider`** from `src/index.ts`.
6. **Add test coverage** — fixture replay test for `supportsLocation` and `getCurrent`.
7. **Update `CHANGELOG.md`** under `[Unreleased]`.

## Non-Goals

- Adding a dedicated China weather bureau provider (e.g. CMA). Open-Meteo already covers Chinese cities; a dedicated provider can be added as PRD-004 if higher accuracy is needed.
- Extending Chinese city coverage beyond the 10 cities in the issue (additional cities can be added incrementally to `cn.json`).
- Building an auto-geocoding layer (Nominatim/HERE/etc.) — coordinate lookup stays file-based for simplicity and offline operation.
- Parity gate updates (fixture for Open-Meteo is hand-crafted with `needs_capture: false`; cross-runtime parity gate integration is deferred to a follow-up).

## Design

### Provider Chain After Change

```
Priority 1    HKO        — Hong Kong (free)
Priority 2    SG NEA     — Singapore (free)
Priority 3    JMA        — Japan (free)
Priority 4    CWA        — Taiwan (key required)
Priority 5    Met Office — UK (key required)
Priority 6    BOM        — Australia (free)
Priority 7    NWS        — USA (free)
Priority 7    MetService — New Zealand (free)
Priority 8    DWD        — Germany (free)
Priority 8    BMKG       — Indonesia (free)
Priority 9    KMA        — South Korea (key required)
Priority 9    TMD        — Thailand (key required)
Priority 10   OWM        — Global (key required)
Priority 11   Open-Meteo — Global (free, zero-config) ← NEW
```

### Open-Meteo API

Endpoint: `https://api.open-meteo.com/v1/forecast`

**Current weather** parameters:
```
current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature
```

**Forecast** parameters:
```
daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset
forecast_days=N
```

Both require `latitude=` and `longitude=`. No API key, no `User-Agent` requirement.

**Response shape (current):**
```json
{
  "latitude": 22.5,
  "longitude": 114.0,
  "current": {
    "time": "2026-01-01T12:00",
    "temperature_2m": 22.5,
    "relative_humidity_2m": 70,
    "weather_code": 1,
    "wind_speed_10m": 12.5,
    "apparent_temperature": 21.0
  },
  "daily": {
    "time": ["2026-01-01"],
    "temperature_2m_max": [25.0],
    "temperature_2m_min": [18.0]
  }
}
```

### WMO Weather Code Mapping

New file: `weather/data/condition_maps/wmo-codes.json`

```
0       → sunny           (Clear sky)
1       → sunny           (Mainly clear)
2       → partly_cloudy
3       → overcast
45, 48  → fog             (Fog / icy fog)
51–57   → drizzle         (Slight/moderate/dense + freezing drizzle)
61, 63  → rain
65, 67  → heavy_rain      (Heavy rain / freezing rain)
66      → rain            (Light freezing rain)
71, 73  → snow
75, 86  → heavy_snow
77      → snow            (Snow grains)
80, 81  → showers
82      → heavy_rain      (Violent showers)
85      → snow            (Slight snow showers)
95, 96, 99 → thunderstorm
```

### `supportsLocation` Logic

Open-Meteo requires lat/lon. The provider resolves coordinates from a merged lookup of all city databases that carry `[lat, lon]` pairs:

1. Direct coordinates on the `Location` object (`location.latitude` / `location.longitude`)
2. `CN_CITIES` (new)
3. `US_NWS_CITIES` (existing)
4. `DE_DWD_CITIES` (existing)
5. `METOFFICE_CITIES` (existing)

Since OWM and every dedicated provider have lower priority numbers (higher priority), Open-Meteo never conflicts with them — it only activates when all higher-priority providers have declined or failed.

### New Files

| File | Purpose |
|------|---------|
| `weather/data/condition_maps/wmo-codes.json` | WMO 4680 code → `WeatherCondition` string |
| `weather/data/cities/cn.json` | 10 Chinese cities with `[lat, lon]` |
| `src/providers/open_meteo.ts` | `OpenMeteoProvider` (Bun/TS) |
| `weather/providers/open_meteo.py` | `OpenMeteoProvider` (Python) |

### Modified Files

| File | Change |
|------|--------|
| `weather/data/location-aliases.json` | Add Chinese city aliases (`sz`, `gz`, `sh`, `bj`, CJK city names, `china` → China) |
| `src/data-loader.ts` | Import `cn.json` + `wmo-codes.json`; export `CN_CITIES` and `WMO_CODE_MAP` |
| `src/bootstrap.ts` | Unconditionally push `new OpenMeteoProvider()` after the key-gated providers |
| `src/index.ts` | Re-export `OpenMeteoProvider` |
| `weather/bootstrap.py` | Unconditionally append `OpenMeteoProvider()` in `_build_providers()` |
| `weather/providers/__init__.py` | Add docstring entry, import, and `__all__` entry for `OpenMeteoProvider` |
| `test/setup.ts` | Add `"open_meteo"` to `PROVIDERS` constant so fixture loader includes it |
| `tests/conftest.py` | Add `"open_meteo"` to `_PROVIDERS` tuple so `mock_http` serves its fixtures |

### Test Assets

| File | Purpose |
|------|---------|
| `fixtures/api-responses/open_meteo/manifest.json` | URL → filename mapping; uses `{ "urls": { "url": "file" } }` format to match `test/setup.ts` / `conftest.py`; `needs_capture: false` (hand-crafted) |
| `fixtures/api-responses/open_meteo/shenzhen-current.json` | Canned current + daily response for Shenzhen |
| `test/providers/open_meteo.test.ts` | `supportsLocation`, `getCurrent` parse, alias matching (Bun) |
| `tests/test_open_meteo.py` | `supports_location`, `get_current` parse, alias matching (Python) |

### Chinese City Data (`cn.json`)

```json
{
  "shenzhen":  [22.5431, 114.0579],
  "guangzhou": [23.1291, 113.2644],
  "shanghai":  [31.2304, 121.4737],
  "beijing":   [39.9042, 116.4074],
  "chengdu":   [30.5728, 104.0668],
  "hangzhou":  [30.2741, 120.1551],
  "wuhan":     [30.5928, 114.3055],
  "xian":      [34.3416, 108.9398],
  "nanjing":   [32.0603, 118.7969],
  "chongqing": [29.4316, 106.9123]
}
```

### `location-aliases.json` additions

```json
"china":      "China",
"cn":         "China",
"中国":        "China",
"zhongguo":   "China",
"shenzhen":   "Shenzhen",
"sz":         "Shenzhen",
"深圳":        "Shenzhen",
"guangzhou":  "Guangzhou",
"gz":         "Guangzhou",
"广州":        "Guangzhou",
"shanghai":   "Shanghai",
"sh":         "Shanghai",
"上海":        "Shanghai",
"beijing":    "Beijing",
"bj":         "Beijing",
"北京":        "Beijing",
"chengdu":    "Chengdu",
"成都":        "Chengdu",
"hangzhou":   "Hangzhou",
"杭州":        "Hangzhou",
"wuhan":      "Wuhan",
"武汉":        "Wuhan",
"xian":       "Xian",
"xi'an":      "Xian",
"西安":        "Xian",
"nanjing":    "Nanjing",
"南京":        "Nanjing",
"chongqing":  "Chongqing",
"重庆":        "Chongqing"
```

> **Collision note:** `sh` is currently not in the aliases file. `sg` is Singapore and `hk` is Hong Kong. `cn` currently maps to nothing. `bj` and `gz` are new. `sh` is unambiguous (no German `sh` mapping exists).

### `open_meteo.ts` Sketch

```typescript
export class OpenMeteoProvider implements IWeatherProvider {
  readonly name = "open-meteo";
  readonly priority = 11;  // catch-all fallback
  readonly supportsForecast = true;
  readonly requiresApiKey = false;

  supportsLocation(location: Location): boolean {
    return this.resolveCoords(location) !== null;
  }

  private resolveCoords(location: Location): [number, number] | null {
    // 1. Direct coordinates
    if (location.latitude != null && location.longitude != null)
      return [location.latitude, location.longitude];

    // 2. Merged city lookup
    const n = location.normalized;
    return CN_CITIES[n]
      ?? US_NWS_CITIES[n]
      ?? DE_DWD_CITIES[n]
      ?? METOFFICE_CITIES[n]
      ?? null;
  }

  async getCurrent(location: Location): Promise<WeatherData> { ... }
  async getForecast(location: Location, days = 7): Promise<WeatherData[]> { ... }
}
```

`getCurrent` calls the forecast endpoint with both `current=...` and `daily=...` (to pick up today's high/low), parses `response.current` plus `response.daily[0]`. Sets `observed_at` from `new Date(current.time)` (ISO string e.g. `"2026-01-01T12:00"`).

`getForecast` calls with `daily=...` only, maps each `daily.time[i]` to a `WeatherData` with `forecast_date`.

The display `location` name is derived from `titleCase(location.normalized)` since Open-Meteo does not return a city name in its response.

> **Wind speed unit note:** Open-Meteo returns `wind_speed_10m` in km/h and it is stored as-is in `WeatherData.wind_speed`. OWM stores m/s in the same field (a documented quirk in `openweathermap.ts`). This cross-provider inconsistency pre-dates this PRD and is not introduced here, but implementors should be aware of it.

## Implementation Plan

### Phase 1 — Data files (no code changes, low risk)

1. Create `weather/data/condition_maps/wmo-codes.json`
2. Create `weather/data/cities/cn.json`
3. Update `weather/data/location-aliases.json` — append Chinese aliases

### Phase 2 — Data loader

4. Add `import cnCitiesRaw` and `import wmoCodesRaw` to `src/data-loader.ts`
5. Export `CN_CITIES: Record<string, [number, number]>` and `WMO_CODE_MAP: Record<string, WeatherCondition>`

### Phase 3 — Provider

6. Create `src/providers/open_meteo.ts` with `OpenMeteoProvider`
7. Implement `supportsLocation`, `resolveCoords`, `getCurrent`, `getForecast`
8. Run `bun run typecheck` — expect 0 errors

### Phase 4 — Integration

9. Update `src/bootstrap.ts` — push `new OpenMeteoProvider()` unconditionally
10. Update `src/index.ts` — add `export { OpenMeteoProvider }`

### Phase 5 — Tests

11. Create `fixtures/api-responses/open_meteo/shenzhen-current.json` (canned response)
12. Create `fixtures/api-responses/open_meteo/manifest.json`
13. Create `test/providers/open_meteo.test.ts`:
    - `supportsLocation` returns `true` for Chinese cities and `false` for unsupported locations
    - `getCurrent` parses Shenzhen fixture correctly (temperature, condition, humidity, feels_like)
    - Alias matching: `"sz"` → resolves via `location-aliases.json` → `"shenzhen"` → supported
14. Run `bun test` — expect all tests pass, 0 failures

### Phase 6 — Docs

15. Append to `CHANGELOG.md` `[Unreleased] > Added` section

## Success Criteria

- `bun run src/cli.ts --location "Shenzhen"` returns weather data with provider `open-meteo`
- `bun run src/cli.ts --location "sz"` (alias) resolves to Shenzhen and returns data
- `bun run src/cli.ts --location "Tokyo"` still returns JMA data (priority 3, not Open-Meteo)
- `bun run src/cli.ts --location "New York"` still returns NWS data (priority 7, not Open-Meteo)
- `bun test` — all existing tests pass; new Open-Meteo tests pass
- `bun run typecheck` — 0 errors
- With `OPENWEATHERMAP_API_KEY` unset, querying any of the 10 Chinese cities succeeds
- Provider count: 13 → 14

## Resolved Decisions

- **`sh` alias** — No conflicts in `location-aliases.json` (confirmed by grep). Added as `"Shanghai"`.
- **`cn` alias** — Unmapped. Added as `"China"` (ISO 3166 country code).
- **`china` key in `cn.json`** — Added `"china": [39.9042, 116.4074]` (Beijing) so `--location China` works without OWM. Capital default is reasonable.
- **`xian` / `xi'an`** — Both alias to canonical `"Xian"` in `location-aliases.json`; `cn.json` key is `"xian"` (no apostrophe). Resolution chain: `parseLocation("Xi'an")` → normalized `"xi'an"` → alias `"Xian"` → normalized `"xian"` → matched in `cn.json`. ✅
- **Chongqing** — Straightforward. `cn.json` key `"chongqing"` matches `location.normalized` after alias resolution.
