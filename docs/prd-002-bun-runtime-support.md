# PRD-002: Bun Runtime Support (Dual-Package)

**Status:** Draft
**Created:** 2026-05-12
**Priority:** High

## Problem Statement

The weather skill is Python-only. NanoClaw agent runs Docker without Python 3, requiring significant architecture changes to support Python. Running Bun (a single-binary JS/TS runtime) would make the skill immediately usable by NanoClaw without Docker modifications.

The broader agent ecosystem spans two runtime worlds:

| Agent | Runtime | Current Integration | Blocker |
|-------|---------|-------------------|---------|
| OpenClaw | Python | `from weather import WeatherSkill` | None — works today |
| Hermes Agent | Python | Same as OpenClaw | None — works today |
| NanoClaw | Bun/Docker (no Python) | None | No Python in container |
| Future agents | Unknown | — | Unknown runtime requirements |

A Bun-only rewrite would break Python agents. A Python-only approach leaves NanoClaw blocked. A dual-package with shared data is the correct tradeoff.

## Goals

1. **Full Bun/TypeScript implementation** — feature parity with Python package for all 13 providers, 3 formatters, Telegram sender, and CLI.
2. **Shared data layer** — extract ~1,300 lines of pure data (location aliases, condition maps, city coordinates) into language-agnostic JSON so both packages consume the same source of truth.
3. **Compiled binary distribution** — `bun build --compile` produces a single `weather` binary for agents that can't install packages (NanoClaw Docker).
4. **Identical CLI interface** — same flags, same output, regardless of runtime.
5. **Updated SKILL.md** — document both Python and Bun integration patterns.
6. **Zero disruption to existing Python users** — `from weather import WeatherSkill` continues to work unchanged.

## Non-Goals

- Replacing the Python package. Both packages are first-class and maintained.
- Adding new providers, formatters, or senders (that's a separate PRD).
- Building a shared library / FFI bridge between Python and Bun (over-engineering).
- npm package publishing (can be added later; compiled binary covers the immediate NanoClaw case).
- Supporting Node.js specifically (Bun is the target runtime; Node compat is a nice-to-have, not a requirement).
- Python→TypeScript transpilation tools (the port is manual for correctness).

## Design

### Repository Structure

```
weather-skill/
├── data/                              # Shared data (language-agnostic JSON)
│   ├── location-aliases.json          # 100+ city aliases (9 regions, 3 scripts)
│   ├── condition-emoji.json           # 34 WeatherCondition → emoji mappings
│   ├── cities/                        # Provider-specific city coordinates
│   │   ├── us-nws.json                # 40+ US cities with lat/lon
│   │   ├── de-dwd.json                # 25+ German cities with lat/lon
│   │   └── jma-area-codes.json        # 15+ Japanese cities with JMA area codes
│   └── condition-maps/                # Provider raw data → WeatherCondition
│       ├── hko-icons.json             # HKO icon filenames → conditions
│       ├── jma-codes.json             # 80+ JMA 3-digit weather codes
│       ├── nws-conditions.json        # NWS condition text keywords
│       ├── sg-nea-forecast.json       # NEA forecast text → conditions
│       ├── owm-codes.json             # 60+ OpenWeatherMap condition codes
│       └── brightsky-conditions.json  # Bright Sky (DWD) condition icons
│
├── weather/                           # Python package (existing, ~7,500 lines)
│   ├── models.py                      # Updated: loads LOCATION_ALIASES from ../data/
│   ├── providers/                     # Existing providers, updated to load maps from ../data/
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

The data that must be extracted from Python source into JSON:

| Source File | Data | Lines | JSON Target |
|-------------|------|-------|-------------|
| `models.py:254-545` | `LOCATION_ALIASES` | ~290 | `data/location-aliases.json` |
| `models.py:37-58` | `CONDITION_EMOJI` | ~20 | `data/condition-emoji.json` |
| `providers/hko.py:23-45` | `HKO_ICON_MAP` | ~20 | `data/condition-maps/hko-icons.json` |
| `providers/jma.py:27-68` | `JMA_AREA_CODES` | ~40 | `data/cities/jma-area-codes.json` |
| `providers/jma.py:72-181` | `JMA_WEATHER_CODE_MAP` | ~110 | `data/condition-maps/jma-codes.json` |
| `providers/us_nws.py:27-78` | `US_CITIES` | ~50 | `data/cities/us-nws.json` |
| `providers/us_nws.py:81-123` | `NWS_CONDITION_MAP` | ~40 | `data/condition-maps/nws-conditions.json` |
| `providers/sg_nea.py:29-53` | `SG_CONDITION_MAP` | ~25 | `data/condition-maps/sg-nea-forecast.json` |
| `providers/de_dwd.py:28-58` | `DE_CITIES` | ~30 | `data/cities/de-dwd.json` |
| `providers/de_dwd.py:62-76` | `BRIGHTSKY_CONDITION_MAP` | ~15 | `data/condition-maps/brightsky-conditions.json` |
| `providers/openweathermap.py:30-94` | `CONDITION_MAP` | ~65 | `data/condition-maps/owm-codes.json` |
| **Total** | | **~705** | |

The remaining ~595 lines of data are condition maps in providers not yet read (CWA, Met Office, BOM, MetService, BMKG, KMA, TMD) — each follows the same dict pattern.

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

Core types mirror the Python dataclasses:

```typescript
// src/types.ts

enum WeatherCondition {
  Clear = "clear",
  Sunny = "sunny",
  PartlyCloudy = "partly_cloudy",
  // ... 34 values matching Python's WeatherCondition enum
}

interface WeatherData {
  location: string;
  temperature: number;
  feelsLike?: number;
  humidity?: number;
  windSpeed?: number;
  windDirection?: string;
  windDescription?: string;
  condition: WeatherCondition;
  description?: string;
  observedAt?: Date;
  forecastDate?: Date;
  tempHigh?: number;
  tempLow?: number;
  precipitationChance?: number;
  aqi?: number;
  aqhi?: number;
  uvIndex?: number;
  providerName: string;
  // ... remaining fields
}

interface Location {
  raw: string;
  city?: string;
  country?: string;
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

Both runtimes must accept identical flags and produce identical output:

```bash
# These must produce the same output:
python -m weather.cli --location "Hong Kong"
bun run src/cli.ts --location "Hong Kong"

# Including:
--location, -l     # Location string
--forecast, -f     # Fetch forecast
--days, -d         # Forecast days (default: 3)
--format           # text | telegram | whatsapp | json
--send             # Send to channel
--chat-id          # Override chat ID
--topic-id         # Telegram topic ID
--provider         # Provider name (default: auto)
--verbose, -v      # Verbose output
```

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

- [ ] `bun run src/cli.ts --location "Hong Kong"` returns HKO data matching Python output
- [ ] `bun run src/cli.ts --location "Tokyo"` returns JMA data
- [ ] `bun run src/cli.ts --location "Singapore"` returns NEA data
- [ ] All 13 providers return data consistent with Python implementations (spot-check per provider)
- [ ] `bun run src/cli.ts --location "Hong Kong" --format telegram` produces valid MarkdownV2
- [ ] `bun run src/cli.ts --location "Hong Kong" --format json` produces valid JSON with same schema
- [ ] `bun run src/cli.ts --location "Hong Kong" --format telegram --send` delivers message to Telegram
- [ ] `bun build src/cli.ts --compile --outfile weather && ./weather --location "Hong Kong"` works
- [ ] Python package continues to work with zero behavioral changes after data extraction
- [ ] Existing Python test suite passes with data loaded from JSON
- [ ] Bun test suite covers all providers, formatters, and CLI
- [ ] SKILL.md documents both integration patterns
- [ ] `data/` JSON files are the single source of truth for location aliases and condition maps

## Open Questions

1. **Python data loading: lazy vs eager?** Should providers load JSON on first call (lazy) or at import time (eager, like current hardcode)? Eager is simpler and matches current behavior, but means every Python invocation reads 7+ JSON files. For a CLI tool, the I/O overhead is negligible.

2. **Formatter utility deduplication.** The Python formatters have duplicated helper methods (`_generate_summary`, `_aqhi_quality`, `_uv_description`) across Telegram and WhatsApp formatters. In Bun, we plan to extract these to `src/utils.ts`. Should we also refactor the Python formatters to use a shared `utils.py`, or accept the asymmetry?

3. **Bun version pinning.** Bun is evolving rapidly. What minimum Bun version should we target? Suggest Bun >= 1.1 (stable `fetch`, `build --compile`, `test` runner).

4. **npm publish scope.** Should the Bun package be published to npm eventually? If so, under what name (`weather-skill`, `@claw/weather-skill`, etc.)? Not blocking for v1 but worth deciding early to avoid renames.

5. **Test data for provider tests.** Provider tests need HTTP mocking. Python tests likely use their own approach. Bun has `bun:test` with built-in mocking. Should test fixture data (mock API responses) also live in `data/` or be duplicated per test suite?

## Phases

| Phase | Scope | Description |
|-------|-------|-------------|
| **1** | Shared data extraction | Extract 7 JSON files from Python source, update Python providers to load from JSON, verify all Python tests pass |
| **2** | Bun scaffold + core types | `package.json`, `tsconfig.json`, `src/types.ts`, `src/models.ts`, data loading utilities |
| **3** | Bun providers (batch 1) | HKO, JMA, SG NEA, US NWS — the 4 largest free providers with diverse API patterns |
| **4** | Bun providers (batch 2) | DWD, BOM, MetService, BMKG, CWA, Met Office, KMA, TMD, OpenWeatherMap |
| **5** | Bun formatters + sender | cli_text, Telegram, WhatsApp formatters + Telegram sender + `src/utils.ts` |
| **6** | Bun CLI + bootstrap | `src/cli.ts`, `src/bootstrap.ts`, compiled binary build |
| **7** | Bun tests | Mirror Python test structure with `bun:test` |
| **8** | Docs + SKILL.md | Update SKILL.md, README, add Bun integration examples |

## Effort Estimate

| Phase | Hours | Notes |
|-------|-------|-------|
| 1 — Shared data | 1.5 | Extract + validate JSON, update Python imports |
| 2 — Scaffold + types | 1 | Package setup, interfaces, model types |
| 3 — Providers batch 1 | 2 | 4 providers, mechanical translation |
| 4 — Providers batch 2 | 2.5 | 9 providers, some with more complex APIs |
| 5 — Formatters + sender | 2 | String formatting, Telegram API |
| 6 — CLI + bootstrap | 1 | Arg parser, factory function, binary build |
| 7 — Tests | 2 | Provider mocks, formatter unit tests, CLI integration |
| 8 — Docs | 0.5 | SKILL.md, README updates |
| **Total** | **~12.5** | |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Provider behavior diverges between Python and Bun | Medium | High — different output for same location | Shared data layer + cross-runtime test assertions (Phase 7) |
| Bun `fetch` handles edge cases differently from `urllib` | Low | Medium — timeout, redirect, encoding differences | Test against live APIs in both runtimes |
| Shared JSON data drifts out of sync | Low | Medium — one package updated, other broken | CI validates both packages against same data files |
| Bun compiled binary size is too large for NanoClaw Docker | Low | High — defeats the purpose | Bench: Bun compiled binaries are typically ~80-120MB. Verify with NanoClaw team. |
| Maintenance burden of two codebases | High | Medium — ongoing cost | Shared data reduces the highest-drift surface. Provider logic is stable and rarely changes. |

## Dependencies

- **Bun >= 1.1** installed in dev environment and CI
- **NanoClaw team confirmation** that a compiled Bun binary (~80-120MB) is acceptable in their Docker image
- **No new Python dependencies** — `json` and `pathlib` are stdlib
