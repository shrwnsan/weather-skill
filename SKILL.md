---
name: weather
description: Get current weather and forecasts for any location, with special support for Hong Kong via HKO API
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

- `@Claw weather` - Current weather for default location (Hong Kong)
- `@Claw weather Tokyo` - Current weather for Tokyo
- `@Claw weather forecast` - 3-day forecast for default location
- `@Claw weather forecast --days 5` - 5-day forecast
- `@Claw 天氣` - Current weather in Chinese (defaults to HK)

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | For Telegram | Telegram bot token |
| `TELEGRAM_CHAT_ID` | For Telegram | Default chat ID |
| `OPENWEATHERMAP_API_KEY` | For global | OpenWeatherMap API key (fallback) |

### Default Behavior

1. **No location specified?** Agent attempts to infer from user context or prompts for location
2. **Hong Kong location?** Uses HKO provider (free, no API key needed)
3. **Global location?** Uses OpenWeatherMap (requires API key)
4. **No OWM API key?** Agent prompts user to sign up at [openweathermap.org/api](https://openweathermap.org/api)

## Providers

| Provider | Coverage | API Key | Priority |
|----------|----------|---------|----------|
| HKO | Hong Kong | Free | 1 (primary for HK) |
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
from skills.weather import WeatherSkill
from skills.weather.providers.hko import HKOProvider
from skills.weather.formatters.telegram import TelegramFormatter
from skills.weather.senders.telegram import TelegramSender

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

Same integration as NanoClaw - import from `skills.weather`.

## Agent Execution

When a user requests weather information, execute the following:

### Current Weather

```bash
python /workspace/group/skills/weather/scripts/weather --location "<location>"
```

### Forecast

```bash
python /workspace/group/skills/weather/scripts/weather --location "<location>" --forecast --days 3
```

### Send to Telegram

```bash
python /workspace/group/skills/weather/scripts/weather --location "<location>" --platform telegram --send
```

### Parse User Input

1. Extract location from user message (or infer from context)
2. Detect if forecast is requested (keywords: "forecast", "預報", "未來幾天")
3. Parse number of days if specified (default: 3, max: 9 for HKO)
4. Execute appropriate command and return output to user

## CLI Usage

```bash
# Current weather
weather --location "Hong Kong"

# Forecast
weather --location "Hong Kong" --forecast --days 5

# JSON output
weather --location "Hong Kong" --format json

# Send to Telegram
weather --location "Hong Kong" --platform telegram --send
```

## File Structure

```
skills/weather/
├── SKILL.md              # This file (skill definition)
├── scripts/              # Executable scripts
│   └── weather           # CLI entry point
├── docs/                 # Documentation
│   └── provider-selection.md
├── references/           # Reference docs
│   ├── ARCHITECTURE.md   # Design documentation
│   └── EXTENDING.md      # Extension guide
├── __init__.py           # Package exports
├── cli.py                # CLI interface
├── models.py             # Data models
├── providers/
│   ├── __init__.py
│   ├── base.py           # WeatherProvider ABC
│   ├── hko.py            # HK Observatory
│   └── openweathermap.py # OpenWeatherMap
├── formatters/
│   ├── __init__.py
│   ├── base.py           # WeatherFormatter ABC
│   └── telegram.py       # Telegram MarkdownV2
└── senders/
    ├── __init__.py
    ├── base.py           # WeatherSender ABC
    └── telegram.py       # Telegram Bot API
```

## Error Handling

- **Provider failure**: Falls back to next provider in chain
- **All providers fail**: Returns error message
- **AQHI unavailable**: Continues with weather, notes in output
- **Network timeout**: Retries with exponential backoff

## License

Apache License 2.0
