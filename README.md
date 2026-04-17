# Weather Skill

A platform-agnostic weather skill for AI agents. Fetches weather data from multiple providers and delivers formatted reports to various messaging platforms.

## Quick Start (Agent Usage)

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

**All environment variables are optional.** 8 of 13 providers work without any API key. The skill outputs to stdout by default — agents capture this and route to their own channels. Env vars are only needed for specific providers or direct Telegram delivery.

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
skill.add_provider(OpenWeatherMapProvider(api_key=os.environ["OPENWEATHERMAP_API_KEY"]))  # Global (priority 10)
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
| SG NEA | Singapore | Free | 2 | 4-day | PSI (1-hr) |
| JMA | Japan | Free | 3 | 7-day | No |
| CWA | Taiwan | Required | 4 | 7-day | No |
| UK Met Office | United Kingdom | Required | 5 | 7-day | No |
| BOM | Australia | Free | 6 | 7-day | No |
| MetService | New Zealand | Free | 7 | Current only | No |
| NWS | USA | Free | 7 | 7-day | No |
| BMKG | Indonesia | Free | 8 | 3-day | No |
| DWD (Bright Sky) | Germany | Free | 8 | 10-day | No |
| KMA | South Korea | Required | 9 | 3-day | No |
| TMD | Thailand | Required | 9 | 7-day | No |
| OpenWeatherMap | Global | Required | 10 | 5-day | AQI via Air Pollution API |

### Provider Selection Logic

1. **Hong Kong locations** → HKO provider (priority 1)
2. **Singapore locations** → SG NEA provider (priority 2)
3. **Japan locations** → JMA provider (priority 3)
4. **Taiwan locations** → CWA provider (priority 4, requires API key)
5. **UK locations** → UK Met Office provider (priority 5, requires API key)
6. **Australia locations** → BOM provider (priority 6)
7. **New Zealand locations** → MetService provider (priority 7, current weather only)
8. **USA locations** → NWS provider (priority 7)
9. **Indonesia locations** → BMKG provider (priority 8)
10. **Germany locations** → DWD provider (priority 8)
11. **South Korea locations** → KMA provider (priority 9, requires API key)
12. **Thailand locations** → TMD provider (priority 9, requires API key)
13. **Other locations** → OpenWeatherMap provider (priority 10, requires API key)

**Location aliases with no dedicated provider** (routed to OpenWeatherMap):
- 🇮🇳 India — 20 cities including Hindi names (दिल्ली, मुंबई) and legacy names (Bombay, Calcutta)
- 🇨🇦 Canada — 15 cities including airport codes (YYZ, YVR, YUL) and French names (Montréal, Québec)

### Default Behavior

- **No location specified?** Agent attempts to infer from user context or prompts for location
- **No OWM API key?** Agent prompts user to sign up (free tier: 1000 calls/day)

## Output Formats

### Telegram / WhatsApp (MarkdownV2 / WhatsApp formatting)

Both platforms share the same structure. WhatsApp uses `*bold*` headers and `_italic_` summaries; Telegram uses MarkdownV2 escaping.

```
🌧️ Hong Kong Weather — Tuesday, March 31

🌡️ 26°C (feels 28°C) • High 30° / Low 23°
🌧️ Rain with thunderstorms possible.
💧 Humidity: 78%
💨 Wind: South force 3
🌧️ Rain chance: 60%
🌬️ Air Quality: Moderate (AQHI 5)
☀️ UV Index: 7.0 (High)
🌅 Sunrise: 6:15 AM | 🌇 Sunset: 6:25 PM

Warm and humid with rain expected — perfect weather for a cozy day indoors.
```

### CLI (Text)

```
🌤️ Weather for Hong Kong
🌡️ Temperature: 26°C
   Feels like: 28°C
   Range: 23° - 30°
💨 Wind: South force 3
💧 Humidity: 78%
🌧️ Rain chance: 60%
☀️ UV Index: 7.0
🌫️ AQHI: 5 (Moderate)
📍 Provider: hko
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHERMAP_API_KEY` | For global | OpenWeatherMap API key |
| `CWA_API_KEY` | For Taiwan | Taiwan CWA API key |
| `METOFFICE_API_KEY` | For UK | UK Met Office API key |
| `KMA_SERVICE_KEY` | For S. Korea | Korea KMA service key |
| `TMD_API_TOKEN` | For Thailand | Thailand TMD API token |

### Free vs Paid Providers

**Free (no API key required):**
- Hong Kong (HKO)
- Singapore (NEA)
- Japan (JMA)
- Australia (BOM)
- New Zealand (MetService)
- USA (NWS)
- Indonesia (BMKG)
- Germany (DWD via Bright Sky)

**Requires API key:**
- Taiwan (CWA) - Sign up at [opendata.cwa.gov.tw](https://opendata.cwa.gov.tw/)
- UK (Met Office) - Sign up at [datahub.metoffice.gov.uk](https://datahub.metoffice.gov.uk/)
- South Korea (KMA) - Sign up at [data.go.kr](https://data.go.kr/)
- Thailand (TMD) - Sign up at [data.tmd.go.th](https://data.tmd.go.th/)
- Global (OpenWeatherMap) - Sign up at [openweathermap.org/api](https://openweathermap.org/api)

### Direct Telegram Delivery (Optional)

The `--send` flag bypasses the agent and sends directly to Telegram. This requires:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Default chat ID |

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

MIT License - See [LICENSE](LICENSE) for details.
