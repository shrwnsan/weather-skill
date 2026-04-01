#!/usr/bin/env python3
"""
Weather Skill CLI interface.


Command-line interface for testing and standalone use of the weather skill.

Usage:
    weather --location "Hong Kong"
    weather --location "Hong Kong" --forecast --days 3
    weather --location "Hong Kong" --platform telegram --send
    weather --help
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Try to import from package, fallback to direct imports
try:
    from .models import WeatherData, WeatherCondition, Location
    from .formatters.telegram import TelegramFormatter
except ImportError:
    # Running as standalone script
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from models import WeatherData, WeatherCondition, Location
        from formatters.telegram import TelegramFormatter
    except ImportError:
        TelegramFormatter = None
        WeatherData = None
        WeatherCondition = None


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="weather",
        description="Fetch weather information for any location",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  weather --location "Hong Kong"
  weather -l "Hong Kong" --forecast --days 5
  weather -l "Hong Kong" --platform telegram
  weather -l "Hong Kong" --format json
  weather -l "Hong Kong" --send --chat-id "-1003858139698"
        """
    )

    parser.add_argument(
        "-l", "--location",
        type=str,
        default="Hong Kong",
        help="Location to fetch weather for (default: Hong Kong)"
    )

    parser.add_argument(
        "-f", "--forecast",
        action="store_true",
        help="Fetch forecast instead of current weather"
    )

    parser.add_argument(
        "-d", "--days",
        type=int,
        default=3,
        help="Number of forecast days (default: 3)"
    )

    parser.add_argument(
        "-p", "--platform",
        type=str,
        choices=["telegram", "text", "json"],
        default="text",
        help="Output format platform (default: text)"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--send",
        action="store_true",
        help="Send to configured channel (requires --platform telegram)"
    )

    parser.add_argument(
        "--chat-id",
        type=str,
        help="Override chat ID for sending"
    )

    parser.add_argument(
        "--topic-id",
        type=int,
        help="Telegram topic/thread ID"
    )

    parser.add_argument(
        "--bot-token",
        type=str,
        help="Telegram bot token (or set TELEGRAM_BOT_TOKEN env)"
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["hko", "auto"],
        default="auto",
        help="Weather provider to use (default: auto)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    return parser


def format_text(data: dict | list) -> str:
    """Simple text formatter for CLI output."""
    if isinstance(data, list):
        lines = ["📊 Weather Forecast\n"]
        for day in data:
            date_str = day.get("forecast_date", "Unknown")
            temp_high = day.get("temp_high", "?")
            temp_low = day.get("temp_low", "?")
            condition = day.get("condition", "Unknown")
            lines.append(f"{date_str}: {temp_high}° / {temp_low}° - {condition}")
        return "\n".join(lines)

    # Single weather data
    lines = []
    lines.append(f"🌤️ Weather for {data.get('location', 'Unknown')}")
    lines.append(f"🌡️ Temperature: {data.get('temperature', '?')}°C")

    if data.get("feels_like"):
        lines.append(f"   Feels like: {data['feels_like']}°C")

    if data.get("temp_high") and data.get("temp_low"):
        lines.append(f"   Range: {data['temp_low']}° - {data['temp_high']}°")

    if data.get("humidity"):
        lines.append(f"💧 Humidity: {data['humidity']}%")

    if data.get("wind_str"):
        lines.append(f"💨 Wind: {data['wind_str']}")

    if data.get("precipitation_chance"):
        lines.append(f"🌧️ Rain chance: {data['precipitation_chance']}%")

    if data.get("uv_index"):
        lines.append(f"☀️ UV Index: {data['uv_index']}")

    if data.get("aqhi"):
        lines.append(f"🌫️ AQHI: {data['aqhi']}")

    lines.append(f"📍 Provider: {data.get('provider_name', 'Unknown')}")

    return "\n".join(lines)


async def fetch_weather(
    location: str,
    forecast: bool = False,
    days: int = 3,
    provider: str = "auto"
) -> dict | list:
    """Fetch weather data using provider classes."""
    try:
        from .providers.hko import HKOProvider
        from .models import Location as WeatherLocation
    except ImportError:
        # Fallback to direct API fetch
        return await _fetch_weather_direct(location, forecast, days)

    # Use HKO provider for Hong Kong
    loc = WeatherLocation(raw=location)
    hko = HKOProvider()

    if not hko.supports_location(loc):
        # For non-HK locations, would use OWM provider
        return await _fetch_weather_direct(location, forecast, days)

    if forecast:
        forecasts = await hko.get_forecast(loc, days)
        return [
            {
                "location": f.location,
                "forecast_date": f.forecast_date.strftime("%Y%m%d") if f.forecast_date else "",
                "temp_high": f.temp_high,
                "temp_low": f.temp_low,
                "condition": f.description or f.condition.value,
                "wind": f.wind_description,
                "precipitation_chance": f.precipitation_chance,
                "humidity": f.humidity,
                "provider_name": f.provider_name,
            }
            for f in forecasts
        ]
    else:
        data = await hko.get_current(loc)
        return {
            "location": data.location,
            "temperature": data.temperature,
            "feels_like": data.feels_like,
            "humidity": data.humidity,
            "temp_high": data.temp_high,
            "temp_low": data.temp_low,
            "icon": None,  # Not used in new system
            "condition": data.description or data.condition.value,
            "wind": data.wind_description,
            "precipitation_chance": data.precipitation_chance,
            "uv_index": data.uv_index,
            "description": data.description,
            "provider_name": data.provider_name,
        }


async def _fetch_weather_direct(
    location: str,
    forecast: bool = False,
    days: int = 3
) -> dict | list:
    """Fallback direct API fetch for when providers aren't available."""
    import urllib.request
    import json

    # HKO API URLs
    CURRENT_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en"
    FORECAST_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"

    if forecast:
        # Fetch forecast
        with urllib.request.urlopen(FORECAST_URL, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        results = []
        for i, fc in enumerate(data.get("weatherForecast", [])[:days]):
            results.append({
                "location": "Hong Kong",
                "forecast_date": fc.get("forecastDate", ""),
                "temp_high": fc.get("forecastMaxtemp", {}).get("value"),
                "temp_low": fc.get("forecastMintemp", {}).get("value"),
                "condition": fc.get("forecastWeather", ""),
                "wind": fc.get("forecastWind", ""),
                "precipitation_chance": _psr_to_percent(fc.get("PSR", "")),
                "provider_name": "hko"
            })
        return results
    else:
        # Fetch current weather
        with urllib.request.urlopen(CURRENT_URL, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        # Parse temperature
        temp = None
        for item in data.get("temperature", {}).get("data", []):
            if item.get("place") == "Hong Kong Observatory":
                temp = item.get("value")
                break

        # Parse humidity
        humidity = None
        for item in data.get("humidity", {}).get("data", []):
            if item.get("place") == "Hong Kong Observatory":
                humidity = item.get("value")
                break

        # Get icon
        icon = data.get("icon", [54])[0] if data.get("icon") else 54

        # Calculate feels-like
        feels_like = temp
        if humidity and humidity > 80 and temp and temp > 25:
            feels_like = temp + 1

        return {
            "location": "Hong Kong",
            "temperature": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "icon": icon,
            "provider_name": "hko"
        }


def _psr_to_percent(psr: str) -> int | None:
    """Map PSR to percentage."""
    psr_map = {
        "low": 10,
        "medium low": 30,
        "medium": 50,
        "medium high": 70,
        "high": 90,
    }
    return psr_map.get(psr.lower())


def _dict_to_weather_data(data: dict) -> "WeatherData":
    """Convert dict to WeatherData object for formatter."""
    if WeatherData is None:
        raise ImportError("WeatherData model not available")

    from datetime import datetime, date

    # Determine condition from icon or text
    condition = WeatherCondition.UNKNOWN if WeatherCondition else None

    # First try icon number (current weather)
    icon_num = data.get("icon", 0)
    if icon_num:
        condition = _hko_icon_to_condition(icon_num)

    # Then try condition text (forecast)
    condition_text = data.get("condition", "")
    if condition_text and WeatherCondition:
        condition = _text_to_condition(condition_text)

    # Parse forecast date
    forecast_date = None
    if data.get("forecast_date"):
        try:
            forecast_date = datetime.strptime(str(data["forecast_date"]), "%Y%m%d").date()
        except ValueError:
            pass

    return WeatherData(
        location=data.get("location", "Unknown"),
        temperature=data.get("temperature", 0),
        feels_like=data.get("feels_like"),
        humidity=data.get("humidity"),
        temp_high=data.get("temp_high") or data.get("temp_high"),
        temp_low=data.get("temp_low") or data.get("temp_low"),
        condition=condition,
        description=data.get("condition") or data.get("description"),
        wind_description=data.get("wind"),
        precipitation_chance=data.get("precipitation_chance"),
        aqhi=data.get("aqhi"),
        uv_index=data.get("uv_index"),
        forecast_date=forecast_date,
        observed_at=datetime.now(),
        provider_name=data.get("provider_name", "unknown")
    )


def _text_to_condition(text: str) -> "WeatherCondition":
    """Map weather text description to WeatherCondition enum."""
    if WeatherCondition is None:
        return None

    text_lower = text.lower()

    # Check for key weather words
    if "thunderstorm" in text_lower or "thunder" in text_lower:
        return WeatherCondition.THUNDERSTORM
    if "heavy rain" in text_lower or "torrential" in text_lower:
        return WeatherCondition.HEAVY_RAIN
    if "rain" in text_lower or "shower" in text_lower:
        return WeatherCondition.RAIN
    if "drizzle" in text_lower:
        return WeatherCondition.DRIZZLE
    if "snow" in text_lower:
        return WeatherCondition.SNOW
    if "fog" in text_lower or "mist" in text_lower:
        return WeatherCondition.FOG
    if "sunny" in text_lower or "fine" in text_lower:
        if "cloudy" in text_lower or "interval" in text_lower:
            return WeatherCondition.PARTLY_CLOUDY
        return WeatherCondition.SUNNY
    if "cloudy" in text_lower or "overcast" in text_lower:
        return WeatherCondition.CLOUDY
    if "windy" in text_lower or "strong wind" in text_lower:
        return WeatherCondition.WINDY
    if "hot" in text_lower:
        return WeatherCondition.HOT
    if "cold" in text_lower or "cool" in text_lower:
        return WeatherCondition.COLD

    return WeatherCondition.UNKNOWN


def _hko_icon_to_condition(icon_num: int) -> "WeatherCondition":
    """Map HKO icon number to WeatherCondition enum."""
    if WeatherCondition is None:
        return None

    # HKO icon mapping: https://www.hko.gov.hk/textonly/v2/explain/wxicon_e.htm
    ICON_MAP = {
        50: WeatherCondition.SUNNY if WeatherCondition else None,
        51: WeatherCondition.SUNNY if WeatherCondition else None,
        52: WeatherCondition.PARTLY_CLOUDY if WeatherCondition else None,
        53: WeatherCondition.PARTLY_CLOUDY if WeatherCondition else None,
        54: WeatherCondition.CLOUDY if WeatherCondition else None,
        55: WeatherCondition.CLOUDY if WeatherCondition else None,
        56: WeatherCondition.OVERCAST if WeatherCondition else None,
        57: WeatherCondition.OVERCAST if WeatherCondition else None,
        58: WeatherCondition.OVERCAST if WeatherCondition else None,
        59: WeatherCondition.OVERCAST if WeatherCondition else None,
        60: WeatherCondition.RAIN if WeatherCondition else None,
        61: WeatherCondition.RAIN if WeatherCondition else None,
        62: WeatherCondition.RAIN if WeatherCondition else None,
        63: WeatherCondition.HEAVY_RAIN if WeatherCondition else None,
        64: WeatherCondition.HEAVY_RAIN if WeatherCondition else None,
        65: WeatherCondition.THUNDERSTORM if WeatherCondition else None,
        66: WeatherCondition.THUNDERSTORM if WeatherCondition else None,
        67: WeatherCondition.THUNDERSTORM if WeatherCondition else None,
        68: WeatherCondition.THUNDERSTORM if WeatherCondition else None,
        69: WeatherCondition.THUNDERSTORM if WeatherCondition else None,
        70: WeatherCondition.FOG if WeatherCondition else None,
        71: WeatherCondition.FOG if WeatherCondition else None,
        72: WeatherCondition.FOG if WeatherCondition else None,
        73: WeatherCondition.FOG if WeatherCondition else None,
        74: WeatherCondition.FOG if WeatherCondition else None,
        75: WeatherCondition.MIST if WeatherCondition else None,
        76: WeatherCondition.CLOUDY if WeatherCondition else None,
        77: WeatherCondition.CLOUDY if WeatherCondition else None,
        78: WeatherCondition.CLOUDY if WeatherCondition else None,
        79: WeatherCondition.UNKNOWN if WeatherCondition else None,
        80: WeatherCondition.WINDY if WeatherCondition else None,
        81: WeatherCondition.WINDY if WeatherCondition else None,
        82: WeatherCondition.WINDY if WeatherCondition else None,
        83: WeatherCondition.WINDY if WeatherCondition else None,
        84: WeatherCondition.UNKNOWN if WeatherCondition else None,
        85: WeatherCondition.UNKNOWN if WeatherCondition else None,
        86: WeatherCondition.UNKNOWN if WeatherCondition else None,
        87: WeatherCondition.UNKNOWN if WeatherCondition else None,
        88: WeatherCondition.UNKNOWN if WeatherCondition else None,
        89: WeatherCondition.UNKNOWN if WeatherCondition else None,
        90: WeatherCondition.HOT if WeatherCondition else None,
        91: WeatherCondition.COLD if WeatherCondition else None,
        92: WeatherCondition.COLD if WeatherCondition else None,
        93: WeatherCondition.COLD if WeatherCondition else None,
        94: WeatherCondition.UNKNOWN if WeatherCondition else None,
        95: WeatherCondition.UNKNOWN if WeatherCondition else None,
        96: WeatherCondition.UNKNOWN if WeatherCondition else None,
        97: WeatherCondition.UNKNOWN if WeatherCondition else None,
        98: WeatherCondition.UNKNOWN if WeatherCondition else None,
        99: WeatherCondition.UNKNOWN if WeatherCondition else None,
    }
    return ICON_MAP.get(icon_num, WeatherCondition.UNKNOWN if WeatherCondition else None)


async def send_telegram(
    message: str,
    bot_token: str,
    chat_id: str,
    topic_id: int | None = None
) -> bool:
    """Send message via Telegram Bot API."""
    import subprocess
    import tempfile

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    if topic_id:
        payload["message_thread_id"] = topic_id

    # Use JSON file approach
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f, ensure_ascii=False)
        temp_path = f.name

    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{temp_path}",
             url],
            capture_output=True,
            text=True,
            timeout=30
        )
        response = json.loads(result.stdout)
        return response.get("ok", False)
    finally:
        os.unlink(temp_path)


async def main(args: argparse.Namespace) -> int:
    """Main entry point."""
    try:
        # Fetch weather
        if args.verbose:
            print(f"Fetching weather for: {args.location}", file=sys.stderr)

        data = await fetch_weather(
            location=args.location,
            forecast=args.forecast,
            days=args.days,
            provider=args.provider
        )

        if args.format == "json":
            print(json.dumps(data, indent=2, default=str))
            return 0

        # Format output
        if args.platform == "telegram":
            # Use Telegram formatter
            if TelegramFormatter is None:
                print("Error: TelegramFormatter not available", file=sys.stderr)
                return 1

            formatter = TelegramFormatter()

            # Convert dict(s) to WeatherData objects
            if isinstance(data, list):
                weather_objs = [_dict_to_weather_data(d) for d in data]
                message = formatter.format_forecast(weather_objs)
            else:
                weather_obj = _dict_to_weather_data(data)
                message = formatter.format_current(weather_obj)
        else:
            message = format_text(data)

        # Print or send
        if args.send:
            bot_token = args.bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
            chat_id = args.chat_id or os.environ.get("TELEGRAM_CHAT_ID")

            if not bot_token:
                print("Error: Telegram bot token required (--bot-token or TELEGRAM_BOT_TOKEN)", file=sys.stderr)
                return 1
            if not chat_id:
                print("Error: Chat ID required (--chat-id or TELEGRAM_CHAT_ID)", file=sys.stderr)
                return 1

            success = await send_telegram(message, bot_token, chat_id, args.topic_id)
            if success:
                print("✓ Message sent successfully", file=sys.stderr)
                return 0
            else:
                print("✗ Failed to send message", file=sys.stderr)
                return 1
        else:
            print(message)
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cli():
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    return asyncio.run(main(args))


if __name__ == "__main__":
    sys.exit(cli())
