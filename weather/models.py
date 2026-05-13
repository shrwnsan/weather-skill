"""
Weather data models for the Weather Skill.

"""

from dataclasses import dataclass, field
from datetime import timezone, datetime, date
from enum import Enum
from typing import Optional


class WeatherCondition(Enum):
    """Standardized weather conditions."""
    CLEAR = "clear"
    SUNNY = "sunny"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    MIST = "mist"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    SHOWERS = "showers"
    HEAVY_RAIN = "heavy_rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    HEAVY_SNOW = "heavy_snow"
    SLEET = "sleet"
    HAIL = "hail"
    WINDY = "windy"
    HOT = "hot"
    COLD = "cold"
    UNKNOWN = "unknown"


from .data.loader import load_json

# Condition to emoji mapping (loaded from weather/data/condition-emoji.json)
CONDITION_EMOJI = {
    WeatherCondition(k): v for k, v in load_json("condition-emoji.json").items()
}


@dataclass
class WeatherData:
    """Standardized weather data structure."""

    # Location (required)
    location: str

    # Current conditions (temperature is required for current weather)
    temperature: float = 0.0  # Celsius

    # Optional location details
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Current conditions (optional)
    feels_like: Optional[float] = None
    humidity: Optional[int] = None  # Percentage
    wind_speed: Optional[float] = None  # km/h
    wind_direction: Optional[str] = None
    wind_description: Optional[str] = None  # Formatted wind string (e.g., "South force 3")
    pressure: Optional[float] = None  # hPa
    visibility: Optional[float] = None  # km
    uv_index: Optional[float] = None

    # Conditions
    condition: WeatherCondition = WeatherCondition.UNKNOWN
    condition_raw: str = ""  # Original condition string from provider
    description: Optional[str] = None  # Detailed description

    # Timestamps
    observed_at: Optional[datetime] = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Forecast-specific
    forecast_date: Optional[date] = None
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    precipitation_chance: Optional[int] = None  # Percentage

    # Air quality (optional)
    aqi: Optional[int] = None  # US EPA Air Quality Index (1-500)
    aqhi: Optional[int] = None  # Air Quality Health Index (1-10+, HK/Canada)
    pm25: Optional[float] = None  # PM2.5 (μg/m³)
    pm10: Optional[float] = None  # PM10 (μg/m³)
    o3: Optional[float] = None  # Ozone (μg/m³)
    no2: Optional[float] = None  # Nitrogen dioxide (μg/m³)

    # Astronomy (optional)
    sunrise: Optional[str] = None  # Time string (e.g., "6:25 AM")
    sunset: Optional[str] = None  # Time string (e.g., "6:35 PM")

    # Provider metadata
    provider_name: str = "unknown"

    @property
    def emoji(self) -> str:
        """Get emoji for current condition."""
        return CONDITION_EMOJI.get(self.condition, "❓")

    @property
    def humidity_str(self) -> str:
        """Human-readable humidity."""
        if self.humidity is None:
            return "N/A"
        return f"{self.humidity}%"

    @property
    def wind_str(self) -> str:
        """Human-readable wind."""
        # Use pre-formatted wind description if available
        if self.wind_description:
            return self.wind_description
        if self.wind_speed is None:
            return "N/A"
        direction = f" {self.wind_direction}" if self.wind_direction else ""
        return f"{self.wind_speed:.0f} km/h{direction}"

    @property
    def temp_range_str(self) -> str:
        """Temperature range for forecast."""
        if self.temp_high is not None and self.temp_low is not None:
            return f"{self.temp_low:.0f}°C - {self.temp_high:.0f}°C"
        return f"{self.temperature:.0f}°C"

    @property
    def aqhi_str(self) -> str:
        """Human-readable AQHI with risk level (HK/Canada scale 1-10+)."""
        if self.aqhi is None:
            return "N/A"
        if self.aqhi <= 3:
            return f"{self.aqhi} (Low)"
        elif self.aqhi <= 6:
            return f"{self.aqhi} (Moderate)"
        elif self.aqhi <= 7:
            return f"{self.aqhi} (High)"
        elif self.aqhi <= 10:
            return f"{self.aqhi} (Very High)"
        else:
            return f"{self.aqhi}+ (Serious)"

    @property
    def aqi_str(self) -> str:
        """Human-readable AQI with category (US EPA scale 1-500)."""
        if self.aqi is None:
            return "N/A"
        if self.aqi <= 50:
            return f"{self.aqi} (Good)"
        elif self.aqi <= 100:
            return f"{self.aqi} (Moderate)"
        elif self.aqi <= 150:
            return f"{self.aqi} (Unhealthy for Sensitive)"
        elif self.aqi <= 200:
            return f"{self.aqi} (Unhealthy)"
        elif self.aqi <= 300:
            return f"{self.aqi} (Very Unhealthy)"
        else:
            return f"{self.aqi} (Hazardous)"

    @property
    def effective_feels_like(self) -> float:
        """Get feels-like temperature, calculating if not provided.

        If feels_like is None, calculates from humidity/wind using
        heat index and wind chill formulas.

        Returns:
            Feels-like temperature in Celsius
        """
        if self.feels_like is not None:
            return self.feels_like

        # Calculate from humidity/wind if available
        if self.humidity is not None:
            wind = self.wind_speed / 3.6 if self.wind_speed else 0.0
            return self._calculate_feels_like(self.temperature, self.humidity, wind)

        return self.temperature

    @staticmethod
    def _calculate_feels_like(temp: float, humidity: int, wind_speed: float = 0.0) -> float:
        """Calculate feels-like temperature using heat index and wind chill.

        Uses simplified NWS/NOAA approach:
        - Heat index: applies when temp >= 27°C and humidity >= 40%
        - Wind chill: applies when temp <= 10°C and wind >= 4.8 km/h

        Args:
            temp: Temperature in Celsius
            humidity: Relative humidity percentage (0-100)
            wind_speed: Wind speed in m/s (not km/h — callers must convert)

        Returns:
            Feels-like temperature in Celsius
        """
        # Heat index for hot/humid conditions
        if temp >= 27 and humidity >= 40:
            # Simplified heat index approximation
            # Based on NWS/NOAA Steadman equation
            hi = temp + (0.1 * humidity) - (0.05 * temp)
            # Clamp to at least temp (feels at least as hot)
            return max(round(hi), round(temp))

        # Wind chill for cold/windy conditions
        if temp <= 10 and wind_speed > 1.33:  # 4.8 km/h = 1.33 m/s
            # Wind chill formula (metric): WC = 13.12 + 0.6215*T - 11.37*V^0.16
            # Where V is wind speed in km/h
            wind_kmh = wind_speed * 3.6
            wc = 13.12 + 0.6215 * temp - 11.37 * (wind_kmh ** 0.16)
            return max(round(wc), round(temp))

        # No adjustment needed
        return round(temp)


@dataclass
class Location:
    """Parsed location information."""

    raw: str  # Original input
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Normalized for provider matching
    normalized: str = ""

    def __post_init__(self):
        if not self.normalized:
            self.normalized = self.raw.lower().strip()


# Common location aliases (loaded from weather/data/location-aliases.json)
LOCATION_ALIASES = load_json("location-aliases.json")


def normalize_location(location: str) -> str:
    """Normalize location string."""
    loc = location.lower().strip()
    return LOCATION_ALIASES.get(loc, location.strip())
