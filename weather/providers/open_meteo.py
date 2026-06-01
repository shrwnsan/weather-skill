"""
Open-Meteo provider — zero-config global fallback.

Free, no API key. Endpoint: api.open-meteo.com/v1/forecast
Requires lat/lon; resolves from the merged city lookup tables.
Priority 11 — lowest in the chain.
"""

import asyncio
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from typing import Optional

from ..data.loader import load_json
from ..models import Location, WeatherCondition, WeatherData
from .base import LocationNotSupportedError, ProviderError, WeatherProvider

# Load city coordinate tables — shared with Bun runtime.
_CN_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "cn.json").items()
}
_US_NWS_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "us-nws.json").items()
}
_DE_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "de-dwd.json").items()
}
_METOFFICE_CITIES: dict[str, tuple[float, float]] = {
    k: tuple(v) for k, v in load_json("cities", "metoffice.json").items()
}

_WMO_CODE_MAP: dict[int, WeatherCondition] = {
    int(k): WeatherCondition(v)
    for k, v in load_json("condition_maps", "wmo-codes.json").items()
}

_BASE_URL = "https://api.open-meteo.com/v1/forecast"
_CURRENT_PARAMS = (
    "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature"
)
_DAILY_PARAMS = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max,sunrise,sunset,uv_index_max"
)


class OpenMeteoProvider(WeatherProvider):
    """
    Open-Meteo weather provider.

    Coverage: Global (via lat/lon lookup)
    API Key: None required
    Priority: 11 (zero-config catch-all fallback below OpenWeatherMap)
    """

    priority = 11
    supports_forecast = True
    supports_air_quality = False
    requires_api_key = False

    @property
    def name(self) -> str:
        return "open-meteo"

    def supports_location(self, location: Location) -> bool:
        return self._resolve_coords(location) is not None

    async def get_current(self, location: Location) -> WeatherData:
        coords = self._resolve_coords(location)
        if coords is None:
            raise LocationNotSupportedError(
                f"Open-Meteo: cannot resolve coordinates for: {location.raw}"
            )
        lat, lon = coords
        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "current": _CURRENT_PARAMS,
            "daily": _DAILY_PARAMS,
            "forecast_days": "1",
            "timezone": "UTC",
        }
        data = await self._fetch(params)
        return self._parse_current(location, data)

    async def get_forecast(
        self, location: Location, days: int = 7
    ) -> list[WeatherData]:
        coords = self._resolve_coords(location)
        if coords is None:
            raise LocationNotSupportedError(
                f"Open-Meteo: cannot resolve coordinates for: {location.raw}"
            )
        lat, lon = coords
        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "daily": _DAILY_PARAMS,
            "forecast_days": str(min(days, 16)),
            "timezone": "UTC",
        }
        data = await self._fetch(params)
        return self._parse_forecast(location, data, days)

    # ── Private helpers ────────────────────────────────────────────────

    def _resolve_coords(
        self, location: Location
    ) -> Optional[tuple[float, float]]:
        if location.latitude is not None and location.longitude is not None:
            return (location.latitude, location.longitude)
        n = location.normalized
        return (
            _CN_CITIES.get(n)
            or _US_NWS_CITIES.get(n)
            or _DE_CITIES.get(n)
            or _METOFFICE_CITIES.get(n)
        )

    async def _fetch(self, params: dict) -> dict:
        url = f"{_BASE_URL}?{urllib.parse.urlencode(params)}"
        loop = asyncio.get_running_loop()

        def fetch():
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                raise ProviderError(f"Open-Meteo API error: HTTP {e.code}")
            except Exception as e:
                raise ProviderError(f"Open-Meteo request failed: {e}")

        return await loop.run_in_executor(None, fetch)

    def _parse_current(self, location: Location, data: dict) -> WeatherData:
        current = data.get("current", {})
        daily = data.get("daily", {})

        wmo_code = current.get("weather_code", 0)
        condition = _WMO_CODE_MAP.get(wmo_code, WeatherCondition.UNKNOWN)

        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip_chances = daily.get("precipitation_probability_max", [])
        uv_indices = daily.get("uv_index_max", [])
        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])
        observed_at = datetime.now(timezone.utc)
        raw_time = current.get("time")
        if isinstance(raw_time, str):
            try:
                observed_at = datetime.fromisoformat(raw_time).replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, TypeError):
                pass

        return WeatherData(
            location=location.normalized.title(),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            temperature=current.get("temperature_2m", 0.0),
            feels_like=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            wind_speed=current.get("wind_speed_10m"),
            temp_high=max_temps[0] if max_temps else None,
            temp_low=min_temps[0] if min_temps else None,
            precipitation_chance=precip_chances[0] if precip_chances else None,
            uv_index=uv_indices[0] if uv_indices else None,
            sunrise=_format_time(sunrises[0]) if sunrises else None,
            sunset=_format_time(sunsets[0]) if sunsets else None,
            condition=condition,
            condition_raw=f"wmo:{wmo_code}",
            observed_at=observed_at,
            provider_name=self.name,
        )

    def _parse_forecast(
        self, location: Location, data: dict, days: int
    ) -> list[WeatherData]:
        daily = data.get("daily", {})
        times: list[str] = daily.get("time", [])
        wmo_codes: list[int] = daily.get("weather_code", [])
        max_temps: list[float] = daily.get("temperature_2m_max", [])
        min_temps: list[float] = daily.get("temperature_2m_min", [])
        precip_chances: list[int] = daily.get("precipitation_probability_max", [])
        uv_indices: list[float] = daily.get("uv_index_max", [])
        sunrises: list[str] = daily.get("sunrise", [])
        sunsets: list[str] = daily.get("sunset", [])

        location_name = location.normalized.title()
        forecasts = []

        for i, date_str in enumerate(times[:days]):
            wmo_code = wmo_codes[i] if i < len(wmo_codes) else 0
            condition = _WMO_CODE_MAP.get(wmo_code, WeatherCondition.UNKNOWN)
            forecasts.append(
                WeatherData(
                    location=location_name,
                    temperature=0.0,
                    condition=condition,
                    condition_raw=f"wmo:{wmo_code}",
                    forecast_date=date.fromisoformat(date_str),
                    temp_high=max_temps[i] if i < len(max_temps) else None,
                    temp_low=min_temps[i] if i < len(min_temps) else None,
                    precipitation_chance=(
                        precip_chances[i] if i < len(precip_chances) else None
                    ),
                    uv_index=uv_indices[i] if i < len(uv_indices) else None,
                    sunrise=_format_time(sunrises[i]) if i < len(sunrises) else None,
                    sunset=_format_time(sunsets[i]) if i < len(sunsets) else None,
                    provider_name=self.name,
                )
            )
        return forecasts


def _format_time(iso: str) -> str:
    """Extract HH:MM from an ISO 8601 timestamp string.

    >>> _format_time("2026-01-01T06:52")
    '06:52'
    """
    m = _TIME_RE.search(iso)
    return m.group(1) if m else iso


import re as _re
_TIME_RE = _re.compile(r"(\d{2}:\d{2})")
