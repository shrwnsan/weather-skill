---
name: weather-skill
description: Retrieves current weather and forecasts for user-specified locations and formats results for chat platforms. Use when users ask about weather conditions, forecast outlooks, AQHI or UV levels, or location-based weather summaries.
compatibility: Designed for Python agent runtimes with network access. Telegram send flow requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
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

| Provider | Coverage | API Key | Priority |
|----------|----------|---------|----------|
| HKO | Hong Kong | Free | 1 (primary for HK) |
| SG NEA | Singapore | Free | 2 |
| JMA | Japan | Free | 3 |
| CWA | Taiwan | Required | 4 |
| UK Met Office | United Kingdom | Required | 5 |
| BOM | Australia | Free | 6 |
| MetService | New Zealand | Free | 7 |
| NWS | USA | Free | 7 |
| BMKG | Indonesia | Free | 8 |
| DWD (Bright Sky) | Germany | Free | 8 |
| KMA | South Korea | Required | 9 |
| TMD | Thailand | Required | 9 |
| OpenWeatherMap | Global | Required | 10 (fallback) |

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

### NanoClaw

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

### OpenClaw

Same integration as NanoClaw - import from `weather`.

## Agent Execution

When a user requests weather information, execute the following:

### Current Weather

```bash
python -m weather.cli --location "<location>"
```

### Forecast

```bash
python -m weather.cli --location "<location>" --forecast --days 3
```

### Send to Telegram

```bash
python -m weather.cli --location "<location>" --format telegram --send
```

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
├── docs/                 # Documentation
│   └── provider-selection.md
├── weather/              # Python package
│   ├── __init__.py       # Package exports
│   ├── cli.py            # CLI interface
│   ├── models.py         # Data models
│   ├── bootstrap.py      # Default skill builder
│   ├── providers/
│   │   ├── hko.py
│   │   ├── sg_nea.py
│   │   ├── jma.py
│   │   ├── tw_cwa.py
│   │   ├── uk_metoffice.py
│   │   ├── au_bom.py
│   │   ├── nz_metservice.py
│   │   ├── us_nws.py
│   │   ├── id_bmkg.py
│   │   ├── de_dwd.py
│   │   ├── kr_kma.py
│   │   ├── th_tmd.py
│   │   └── openweathermap.py
│   ├── formatters/
│   │   ├── telegram.py
│   │   ├── whatsapp.py
│   │   └── cli_text.py
│   └── senders/
│       └── telegram.py
└── tests/                # Test suite
```

## Error Handling

- **Provider failure**: Falls back to next provider in chain
- **All providers fail**: Returns error message
- **AQHI unavailable**: Continues with weather, notes in output
- **Network timeout**: Retries with exponential backoff

## License

MIT License
