# PRD-004: Air Quality Enrichment Layer

**Status:** Draft — design reference only; implementation deferred
**Created:** 2026-06-01
**Priority:** Low
**Depends on:** #46 (UV index — merged)

## Problem Statement

Air quality data is available for only 3 of 14 providers:

| Provider | Coverage | AQ Source | Scale |
|----------|----------|-----------|-------|
| HKO | Hong Kong | Inline in weather response | AQHI (1–10+) |
| SG NEA | Singapore | Inline in weather response | PSI → mapped to AQI |
| OpenWeatherMap | Global (key required) | Separate `/air_pollution` endpoint | AQI (US EPA 1–500) |

All other providers (JMA, KMA, Met Office, DWD, NWS, BOM, MetService, BMKG, TMD, CWA, Open-Meteo) return **no air quality data**. This means Tokyo, Seoul, London, Berlin, New York, Sydney, Auckland, Jakarta, Bangkok, Taipei, and all Chinese cities served by Open-Meteo lack AQI in their output — even though free global AQI data exists and could fill the gap.

### Why adding AQI only to Open-Meteo is insufficient

A naive approach would add AQI fetching inside the Open-Meteo provider (like OWM does with its separate air pollution endpoint). However, Open-Meteo is **priority 11** — the catch-all fallback. Most major cities have a higher-priority dedicated provider that wins first:

```
Tokyo     → JMA (priority 3) wins → no AQI → Open-Meteo AQI never reached
Seoul     → KMA (priority 9) wins → no AQI → Open-Meteo AQI never reached
London    → Met Office (priority 5) wins → no AQI
New York  → NWS (priority 7) wins → no AQI
Berlin    → DWD (priority 8) wins → no AQI
```

Adding AQI inside Open-Meteo alone only helps locations that **already fall through** to it (Chinese cities, etc.). The architectural fix is a **post-fetch enrichment step** that runs after any provider returns weather data.

## Proposed Architecture

### Enrichment flow

```
getCurrent(location)
  │
  ├─ Provider chain → [JMA / HKO / NWS / Open-Meteo / ...] → WeatherData
  │                                                              │
  │                                           ┌────────────────┘
  │                                           ▼
  │                                   enrichWithAirQuality(data)
  │                                           │
  │                                   ┌───────┴────────┐
  │                                   │  AQ enricher     │
  │                                   │  (independent    │
  │                                   │   data source)    │
  │                                   └───────┬────────┘
  │                                           │
  │                                   merge aqi/pm25/etc.
  │                                   into WeatherData
  │                                           │
  │                                           ▼
  └───────────────────────────────── enriched WeatherData
```

Key properties:
- **Provider-agnostic** — runs regardless of which weather provider won
- **Graceful degradation** — if AQI fetch fails, return weather data unchanged
- **Only enriches when provider didn't already supply AQI/AQHI** — don't overwrite HKO's AQHI or NEA's PSI
- **Optional at the skill level** — controlled by whether an AQI enricher is registered in bootstrap

### Data source: Open-Meteo Air Quality API

The natural first source is Open-Meteo's own Air Quality API:

| Property | Value |
|----------|-------|
| Endpoint | `https://air-quality-api.open-meteo.com/v1/air-quality` |
| Auth | None (free for non-commercial use) |
| Coverage | Global |
| Resolution | 45 km (CAMS global) / 11 km (CAMS Europe) |
| Update cadence | Every 12 hours (global) / 24 hours (Europe) |
| Forecast range | Up to 5 days |
| Key variables | `us_aqi`, `pm2_5`, `pm10`, `ozone`, `nitrogen_dioxide`, `sulphur_dioxide`, `carbon_monoxide` |

**Why this source:**
- Same provider ecosystem as the existing Open-Meteo weather fallback — no new dependency relationship
- Free, no API key — consistent with the project's zero-config philosophy
- Returns US EPA AQI scale — matches the `aqi` field already used by OWM and NEA
- Returns individual pollutant concentrations — populates `pm25`, `pm10`, `o3`, `no2` fields

**Limitations (documented for future consideration):**
- Model-based (CAMS forecast), not real monitoring station data — less precise for specific neighborhoods
- 45 km global resolution — adequate for "haze day?" indication, not for "what's the PM2.5 at my apartment?"
- 12-hour update cadence — not real-time

**Future extensibility:** The enricher interface should be source-agnostic. WAQI (World Air Quality Index), aqicn.org, or government station APIs could be added as alternative or fallback enrichers without changing the orchestration layer.

### AQI enrichment mapping

Open-Meteo returns `us_aqi` (consolidated US EPA index). Mapping to existing `WeatherData` fields:

| Open-Meteo variable | WeatherData field | Notes |
|--------------------|-------------------|-------|
| `us_aqi` | `aqi` | US EPA scale 0–500 — matches existing OWM convention |
| `pm2_5` | `pm25` | μg/m³ |
| `pm10` | `pm10` | μg/m³ |
| `ozone` | `o3` | μg/m³ |
| `nitrogen_dioxide` | `no2` | μg/m³ |
| `sulphur_dioxide` | _(no field)_ | Could add `so2` to WeatherData if needed |
| `carbon_monoxide` | _(no field)_ | Could add `co` to WeatherData if needed |

### Enricher interface

```typescript
// src/types.ts
interface IAirQualityEnricher {
  readonly name: string;
  enrich(data: WeatherData): Promise<WeatherData>;
}
```

```python
# weather/providers/base.py
class AirQualityEnricher(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def enrich(self, data: WeatherData) -> WeatherData: ...
```

The enricher receives the already-populated `WeatherData` from the weather provider and returns a new object with AQI fields filled in. If coordinates are missing (unlikely but defensive) or the fetch fails, it returns the data unchanged.

### Orchestrator changes

In `WeatherSkill.getCurrent()` (and `getForecast()`), after a provider returns data:

```typescript
// src/skill.ts — getCurrent()
const data = await this.getCurrentFromProvider(location, providerName);
return this._enrichers.length > 0
  ? this.applyEnrichers(data)
  : data;
```

`applyEnrichers()` iterates registered enrichers, passing data through each. Each enricher only merges if the target fields are empty:

```typescript
private async applyEnrichers(data: WeatherData): Promise<WeatherData> {
  let result = data;
  for (const enricher of this._enrichers) {
    result = await enricher.enrich(result);
  }
  return result;
}
```

### Bootstrap registration

```typescript
// src/bootstrap.ts
export function buildEnrichers(): IAirQualityEnricher[] {
  const enrichers: IAirQualityEnricher[] = [];
  // Open-Meteo AQI enricher is always available (no key needed)
  enrichers.push(new OpenMeteoAqiEnricher());
  return enrichers;
}
```

In `buildDefaultSkill()`:
```typescript
export function buildDefaultSkill(): WeatherSkill {
  return new WeatherSkill({
    providers: buildProviders(),
    formatters: buildFormatters(),
    senders: buildSenders(),
    enrichers: buildEnrichers(),  // new
  });
}
```

## Scope

### In scope
- `OpenMeteoAqiEnricher` implementation (Bun + Python)
- `IAirQualityEnricher` / `AirQualityEnricher` interface (Bun + Python)
- Orchestrator enrichment pass in `getCurrent()` (Bun + Python)
- Bootstrap registration (`buildEnrichers()`)
- Test fixtures for Open-Meteo AQI API response
- Unit tests for enricher (skip enrichment when AQI/AQHI already present, handle missing coords gracefully, parse AQI response correctly)
- Update `docs/provider-selection.md` Air Quality section

### Out of scope
- Enrichment for `getForecast()` entries (deferred — AQI forecast is less critical than current)
- WAQI / aqicn.org / government station integrations
- Adding `so2` / `co` to `WeatherData` (no formatter support yet)
- Pollen data (Open-Meteo supports it but only for Europe)

## Implementation notes

### Request shape

```
GET https://air-quality-api.open-meteo.com/v1/air-quality
  ?latitude=22.54&longitude=114.06
  &current=us_aqi,pm2_5,pm10,ozone,nitrogen_dioxide
  &timezone=auto
```

Response (abbreviated):
```json
{
  "current": {
    "us_aqi": 42,
    "pm2_5": 12.3,
    "pm10": 28.1,
    "ozone": 45.0,
    "nitrogen_dioxide": 22.7
  }
}
```

### Skip conditions

The enricher should be a no-op when:
1. `data.aqi` is already set (OWM, NEA already provided it)
2. `data.aqhi` is already set (HKO already provided it)
3. `latitude` / `longitude` is missing from the weather data (can't make AQI request)
4. The AQI API fetch fails (return data unchanged — weather is more important than AQI)

### Existing infrastructure leveraged

- `WeatherData.aqi`, `pm25`, `pm10`, `o3`, `no2` — already defined in types
- `aqiQuality()`, `aqiStr()` — quality descriptions already implemented
- CLI, Telegram, WhatsApp formatters — already render AQI when present
- Open-Meteo coordinate resolution — reuse `resolveCoords()` logic from existing provider

## Recommendation: Defer implementation

The enrichment architecture is sound but the data source (CAMS global forecast, 45 km resolution) undermines the value for the primary use case. AQI-sensitive users — someone deciding whether to jog in Shenzhen or mask up in Beijing — need real monitoring station data, not model approximations.

**Proposed path when AQI demand surfaces:**
1. Use WAQI / aqicn.org as the enricher source (real station data, free tier at 1 req/min, covers exactly the cities where users care about AQI)
2. Keep the enrichment layer architecture from this PRD — same interface, same orchestrator pass, swap the data source
3. CAMS (Open-Meteo AQI API) remains available as a fallback source if station data is unavailable for a given location

This PRD is retained as a design reference for that future work.

## Risks

| Risk | Mitigation |
|------|------------|
| Extra latency from second API call | AQI fetch runs after weather data is already available; timeout bounded (5 s). Worst case: weather returns without AQI. |
| CAMS model accuracy | Document as model-based, 45 km resolution. Adequate for trend/haze indication. Real station data is a future enhancement. |
| Breaking cross-runtime parity | Enricher must be implemented in both runtimes simultaneously, with matching test fixtures. |
| Open-Meteo AQI API downtime | Enricher is optional and graceful — weather data is returned regardless. |

## Effort estimate

| Component | Effort |
|-----------|--------|
| Enricher interface + OpenMeteoAqiEnricher (TS) | ~30 min |
| OpenMeteoAqiEnricher (Python) | ~20 min |
| Orchestrator enrichment pass (TS + Python) | ~20 min |
| Bootstrap registration (TS + Python) | ~10 min |
| Test fixtures + tests (TS + Python) | ~30 min |
| Provider-selection doc update | ~10 min |
| **Total** | **~2 hours** |
