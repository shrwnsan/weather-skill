# API Response Fixtures

Canned HTTP responses for cross-runtime parity testing (PRD-002 Phase 7).

## Layout

```
fixtures/
└── api-responses/
    ├── hko/
    │   ├── manifest.json        # URL → file mapping + capture metadata
    │   └── one_json.json        # captured response
    ├── jma/
    │   ├── manifest.json
    │   ├── forecast-130000.json
    │   └── overview-130000.json
    ├── sg_nea/
    │   ├── manifest.json
    │   ├── air-temperature.json
    │   ├── relative-humidity.json
    │   ├── wind-direction.json
    │   ├── wind-speed.json
    │   ├── 24hr-forecast.json
    │   ├── four-day-outlook.json
    │   └── psi.json
    ├── us_nws/
    │   ├── manifest.json
    │   ├── points.json
    │   ├── stations.json
    │   ├── observations.json
    │   └── forecast.json
    └── openweathermap/
        └── manifest.json        # responses NOT yet captured (needs API key)
```

## Distribution

These fixtures are intentionally **NOT** shipped with the published packages:

- **Python wheel** — `pyproject.toml` only lists the `weather.*` packages, so `fixtures/` at repo root is automatically excluded.
- **npm package** — `package.json` `files` whitelist contains only `src/` and `weather/data/`, so `fixtures/` is automatically excluded.

## Capturing / refreshing

```bash
# All free providers (HKO, JMA, SG NEA, US NWS):
bash scripts/capture-fixtures.sh

# Just one provider:
bash scripts/capture-fixtures.sh hko

# OpenWeatherMap requires a key:
OPENWEATHERMAP_API_KEY=xxx bash scripts/capture-fixtures.sh openweathermap
```

The script is idempotent and pretty-prints all captured JSON for clean diffs. SG NEA is rate-limited (HTTP 429) on aggressive bursts, so the script sleeps 1 s between requests.

## Manifest format

Each `manifest.json` maps the full request URL → the relative filename of its captured response:

```json
{
  "provider": "<name>",
  "description": "...",
  "captured_at": "YYYY-MM-DD",
  "urls": {
    "https://example.com/api/endpoint": "endpoint.json"
  }
}
```

Used by:

- **Phase 7.2** — `tests/conftest.py` `mock_http` fixture (patches `urllib.request.urlopen`).
- **Phase 7.3** — `test/setup.ts` Bun `mock.module()` fetch mock.

For OpenWeatherMap, URLs use `<API_KEY>` as a placeholder; the mock infrastructure must substitute the actual key when matching incoming requests.

## When to refresh

Refresh when:

- A new provider is added to the v0.1 batch.
- A provider's API contract changes (new fields, removed fields, renamed endpoints).
- A captured response shape is too stale to represent realistic data.

Do **not** refresh just because the temperature or weather changed — fixtures are deliberately stable snapshots used with frozen-clock parity tests (`2026-01-01T00:00:00Z` per PRD §Clock Mocking).
