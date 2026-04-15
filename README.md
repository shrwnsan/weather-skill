# Weather Skill

A platform-agnostic weather skill for AI agents. Fetches weather data from multiple providers and delivers formatted reports to various messaging platforms.

## Quick Start

```bash
# Current weather (uses agent location or prompts user)
python -m weather.cli

# Specific location
python -m weather.cli --location "Hong Kong"

# 3-day forecast
python -m weather.cli --location "Tokyo" --forecast --days 3

# Telegram format
python -m weather.cli --location "Hong Kong" --platform telegram

# Send to Telegram
python -m weather.cli --location "Hong Kong" --platform telegram --send
```

## Usage Examples

### CLI

```bash
# Basic current weather
weather -l "Hong Kong"

# Forecast with specific days
weather -l "Hong Kong" --forecast --days 5

# JSON output for piping
weather -l "Hong Kong" --format json

# Send directly to Telegram group
weather -l "Hong Kong" --platform telegram --send --chat-id "<YOUR_CHAT_ID>"
```

### Python API

```python
from weather import WeatherSkill
from weather.providers.hko import HKOProvider
from weather.providers.openweathermap import OpenWeatherMapProvider
from weather.formatters.telegram import TelegramFormatter
from weather.senders.telegram import TelegramSender

# Initialize with providers
skill = WeatherSkill()
skill.add_provider(HKOProvider())  # Hong Kong (priority 1)
skill.add_provider(OpenWeatherMapProvider(api_key="your-api-key"))  # Global (priority 10)
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

## Providers

| Provider | Coverage | API Key | Priority | Forecast | Air Quality |
|----------|----------|---------|----------|----------|-------------|
| HKO | Hong Kong | Free | 1 | 9-day | AQHI (HK scale) |
| BOM | Australia | Free | 6 | 7-day | No |
| MetService | New Zealand | Free | 7 | Current only | No |
| NWS | USA | Free | 7 | 7-day | No |
| OpenWeatherMap | Global | Required | 10 | 5-day | AQI via Air Pollution API |

### Provider Selection Logic

1. **Hong Kong locations** → HKO provider (priority 1)
2. **Australia locations** → BOM provider (priority 6)
3. **New Zealand locations** → MetService provider (priority 7, current weather only)
4. **USA locations** → NWS provider (priority 7)
5. **Other locations** → OpenWeatherMap provider (priority 10, requires API key)

### Default Behavior

- **No location specified?** Agent attempts to infer from user context or prompts for location
- **No OWM API key?** Agent prompts user to sign up (free tier: 1000 calls/day)

## Output Formats

### Telegram (MarkdownV2)

```
🌧️ Hong Kong Weather — Tuesday, Mar 31

🌡️ 26°C (feels 26°C) • High 28° / Low 23°
🌧️ Rain
💧 Humidity: 78% | 💨 Wind: South force 3
🌧️ Rain: 60% | 🌫️ AQHI: 5 (Moderate)
☀️ UV: 7 (High)
```

### CLI (Text)

```
🌤️ Weather for Hong Kong
🌡️ Temperature: 26°C
💧 Humidity: 78%
📍 Provider: hko
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | For Telegram | Telegram bot token |
| `TELEGRAM_CHAT_ID` | For Telegram | Default chat ID |
| `OPENWEATHERMAP_API_KEY` | For global | OpenWeatherMap API key |

### Free vs Paid Providers

**Free (no API key required):**
- Hong Kong (HKO)
- Australia (BOM)
- New Zealand (MetService)
- USA (NWS)

**Requires API key:**
- Global (OpenWeatherMap) - Sign up at [openweathermap.org/api](https://openweathermap.org/api)

### Default Location

Default location is **Hong Kong**. The HKO provider is used automatically for HK locations.

## Documentation

- [Provider Selection](docs/provider-selection.md) — How HKO/OWM selection works, feels-like calculation, air quality

## File Structure

```
weather-skill/
├── SKILL.md              # Skill definition (triggers, instructions)
├── README.md             # This file
├── docs/                 # Documentation
│   └── provider-selection.md
├── weather/              # Python package (single source of truth)
│   ├── cli.py            # CLI implementation
│   ├── models.py         # Data models
│   ├── skill.py          # WeatherSkill orchestrator
│   ├── providers/        # Weather data providers
│   ├── formatters/       # Output formatters
│   └── senders/          # Message senders
└── tests/                # Test suite
```

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
