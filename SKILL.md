---
name: weather-skill
description: Retrieves current weather and forecasts for user-specified locations and formats results for chat platforms. Use when users ask about weather conditions, forecast outlooks, AQHI or UV levels, or location-based weather summaries.
compatibility: Available as both a Python package (13 providers) and a Bun/TypeScript package (5 providers, also distributed as a standalone Linux x86-64 binary that needs no runtime install). Telegram send flow requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
---

# Weather Skill

A platform-agnostic weather skill for AI agents. Fetches weather data from multiple providers and delivers formatted reports to various messaging platforms.

## Triggers

- `weather [location]`
- `weather forecast [location]`
- `天氣` (Chinese for weather)

## Overview

This skill provides weather information for any location, with special support for Hong Kong via the Hong Kong Observatory (HKO) API.

## Usage

```
@agent weather [location]
@agent weather forecast [location]
@agent weather forecast [location] --days 5
```

### Examples

- `@agent weather` - Current weather for default location (Hong Kong)
- `@agent weather Tokyo` - Current weather for Tokyo
- `@agent weather forecast` - 3-day forecast for default location
- `@agent weather forecast --days 5` - 5-day forecast
- `@agent 天氣` - Current weather in Chinese (defaults to HK)

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | For Telegram | Telegram bot token |
| `TELEGRAM_CHAT_ID` | For Telegram | Default chat ID |
| `OPENWEATHERMAP_API_KEY` | For global | OpenWeatherMap API key (fallback) |
| `CWA_API_KEY` | For Taiwan | Taiwan CWA API key |
| `METOFFICE_API_KEY` | For UK | UK Met Office API key |
| `KMA_SERVICE_KEY` | For S. Korea | Korea KMA service key |
| `TMD_API_TOKEN` | For Thailand | Thailand TMD API token |

### Default Behavior

1. **No location specified?** Agent attempts to infer from user context or prompts for location
2. **Provider auto-selection?** `--provider auto` uses the full provider chain — selects the highest-priority provider matching the location
3. **No API key for required provider?** Falls back to next provider in chain
4. **No OWM API key?** Agent prompts user to sign up at [openweathermap.org/api](https://openweathermap.org/api)

## Providers

The Bun/TypeScript package (`@shrwnsan/weather-skill`) currently ships **5 of 13** providers (the four most-popular free regional providers + OpenWeatherMap as the global fallback). The remaining 8 providers are Python-only; porting them is tracked under PRD-002b.

| Provider | Coverage | API Key | Priority | Bun |
|----------|----------|---------|----------|-----|
| HKO | Hong Kong | Free | 1 (primary for HK) | ✅ |
| SG NEA | Singapore | Free | 2 | ✅ |
| JMA | Japan | Free | 3 | ✅ |
| CWA | Taiwan | Required | 4 | — Python only |
| UK Met Office | United Kingdom | Required | 5 | — Python only |
| BOM | Australia | Free | 6 | — Python only |
| MetService | New Zealand | Free | 7 | — Python only |
| NWS | USA | Free | 7 | ✅ |
| BMKG | Indonesia | Free | 8 | — Python only |
| DWD (Bright Sky) | Germany | Free | 8 | — Python only |
| KMA | South Korea | Required | 9 | — Python only |
| TMD | Thailand | Required | 9 | — Python only |
| OpenWeatherMap | Global | Required | 10 (fallback) | ✅ |

## Output Formats

### Telegram (MarkdownV2)

```
⛅ Hong Kong Weather — Tuesday, Mar 31

🌡️ 26°C (feels 26°C) • High 28° / Low 23°
⛅ Partly Cloudy
💧 Humidity: 80% | 💨 Wind: South force 3
🌧️ Rain: 60% | 🌫️ AQHI: 5 (Moderate)
☀️ UV: 7 (High)
```

### CLI (Text)

```
🌤️ Weather for Hong Kong
🌡️ Temperature: 26°C
💧 Humidity: 80%
📍 Provider: hko
```

## Integration

### Python (OpenClaw, Hermes Agent, any Python runtime)

```python
from weather import WeatherSkill
from weather.providers.hko import HKOProvider
from weather.formatters.telegram import TelegramFormatter
from weather.senders.telegram import TelegramSender

# Initialize
skill = WeatherSkill()
skill.add_provider(HKOProvider())
skill.add_formatter("telegram", TelegramFormatter())
skill.add_sender("telegram", TelegramSender(
    bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
    default_chat_id=os.environ["TELEGRAM_CHAT_ID"]
))

# Fetch and send
data = await skill.get_current("Hong Kong")
message = skill.format(data, platform="telegram")
await skill.send(message, channel="telegram")
```

### Bun / TypeScript (NanoClaw, any Bun runtime, Docker images without Python)

```typescript
import { buildDefaultSkill } from "@shrwnsan/weather-skill";

// Built-in factory — registers HKO, JMA, SG NEA, NWS, and OWM (if
// OPENWEATHERMAP_API_KEY is set); registers the three formatters
// unconditionally and TelegramSender iff TELEGRAM_BOT_TOKEN is set.
const skill = buildDefaultSkill();

const data = await skill.getCurrent("Hong Kong");
const message = skill.format(data, "telegram");
await skill.send(message, "telegram");
```

For a manual provider chain (mirrors the Python example above):

```typescript
import {
  WeatherSkill,
  HKOProvider,
  TelegramFormatter,
  TelegramSender,
} from "@shrwnsan/weather-skill";

const skill = new WeatherSkill();
skill.addProvider(new HKOProvider());
skill.addFormatter("telegram", new TelegramFormatter());
skill.addSender("telegram", new TelegramSender({
  bot_token: process.env.TELEGRAM_BOT_TOKEN!,
  default_chat_id: process.env.TELEGRAM_CHAT_ID!,
}));
```

### Compiled binary (no runtime install)

A standalone, statically-linked Linux x86-64 binary (`weather-linux-x64`, ~90 MB) is built by `bun build src/cli.ts --compile --target=bun-linux-x64`. It bundles the Bun runtime + all `weather/data/*.json` and runs anywhere with `glibc` — no Python, no Bun, no `npm install`. A Darwin arm64 build (`weather-darwin-arm64`, ~61 MB) is also produced. Either binary supports the exact same CLI flags as the Python `weather` script:

```bash
./weather-linux-x64 --location "Hong Kong"
./weather-linux-x64 --location "Tokyo" --forecast --days 5
./weather-linux-x64 --location "Hong Kong" --format json
```

## Agent Execution

When a user requests weather information, execute one of the following depending on what's available in the agent's runtime image:

### Current Weather

```bash
# Python install
python -m weather.cli --location "<location>"

# Bun install
bun x @shrwnsan/weather-skill --location "<location>"

# Standalone binary (no install)
./weather-linux-x64 --location "<location>"
```

### Forecast

```bash
python -m weather.cli --location "<location>" --forecast --days 3
# or any of the Bun / binary variants above with the same flags
```

### Send to Telegram

```bash
python -m weather.cli --location "<location>" --format telegram --send
# or any of the Bun / binary variants above with the same flags
```

All three runtimes (Python, Bun, compiled binary) produce **byte-identical** `--format json` output for the same fixture data + frozen clock, guaranteed by the cross-runtime parity CI gate (PRD-002 Phase 7.7).

## Safety Guardrails

1. Default to read-only weather retrieval and formatting.
2. Execute outbound actions (`--send`) only when the user explicitly asks to send.
3. Before sending, confirm destination details (chat/channel and location) if not explicitly provided.
4. Never print, log, or echo secrets (API keys, bot tokens, chat IDs).

### Parse User Input

1. Extract location from user message (or infer from context for read-only weather requests)
2. Detect if forecast is requested (keywords: "forecast", "預報", "未來幾天")
3. Parse number of days if specified (default: 3, max: 9 for HKO)
4. For send actions, require explicit user intent before running `--send`
5. Execute appropriate command and return output to user

## CLI Usage

```bash
# Current weather
weather --location "Hong Kong"

# Forecast
weather --location "Hong Kong" --forecast --days 5

# JSON output
weather --location "Hong Kong" --format json

# Send to Telegram
weather --location "Hong Kong" --format telegram --send
```

## File Structure

```
weather-skill/
├── SKILL.md              # This file (skill definition)
├── README.md             # Install / usage / providers
├── CHANGELOG.md
├── pyproject.toml        # Python packaging
├── package.json          # Bun packaging (@shrwnsan/weather-skill)
├── docs/
│   ├── provider-selection.md
│   ├── prd-002-bun-runtime-support.md
│   └── tasks-002-prd-002-bun-runtime-support.md
├── weather/              # Python package (13 providers)
│   ├── cli.py
│   ├── models.py
│   ├── bootstrap.py
│   ├── data/             # Shared JSON data (loaded by both runtimes)
│   ├── providers/        # 13 providers (hko, sg_nea, jma, tw_cwa,
│   │                     #   uk_metoffice, au_bom, nz_metservice,
│   │                     #   us_nws, id_bmkg, de_dwd, kr_kma,
│   │                     #   th_tmd, openweathermap)
│   ├── formatters/       # telegram, whatsapp, cli_text
│   └── senders/          # telegram
├── src/                  # Bun/TypeScript package (5 providers in v0.1)
│   ├── cli.ts
│   ├── bootstrap.ts
│   ├── skill.ts
│   ├── models.ts
│   ├── types.ts
│   ├── data-loader.ts    # JSON-module imports of weather/data/*
│   ├── providers/        # hko, sg_nea, jma, us_nws, openweathermap
│   ├── formatters/       # cli_text, telegram, whatsapp
│   └── senders/          # telegram
├── tests/                # Python test suite (pytest)
├── test/                 # Bun test suite (bun:test)
└── fixtures/             # Cross-runtime test fixtures + parity snapshots
    ├── api-responses/    # Canned provider responses (mock_http / mockFetch)
    └── parity/           # Phase 7.7 byte-equality snapshots
```

## Error Handling

- **Provider failure**: Falls back to next provider in chain
- **All providers fail**: Returns error message
- **AQHI unavailable**: Continues with weather, notes in output
- **Network timeout**: Retries with exponential backoff

## License

MIT License
