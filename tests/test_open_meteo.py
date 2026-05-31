"""Open-Meteo provider tests (PRD-003)."""

from datetime import date

import pytest

from weather.models import Location, WeatherCondition
from weather.providers.open_meteo import OpenMeteoProvider


class TestSupportsLocation:
    def test_chinese_city(self):
        loc = Location(raw="Shenzhen", normalized="shenzhen")
        assert OpenMeteoProvider().supports_location(loc) is True

    def test_us_city(self):
        loc = Location(raw="New York", normalized="new york")
        assert OpenMeteoProvider().supports_location(loc) is True

    def test_unknown_city(self):
        loc = Location(raw="Atlantis", normalized="atlantis")
        assert OpenMeteoProvider().supports_location(loc) is False

    def test_nanshan_district(self):
        loc = Location(raw="Nanshan", normalized="nanshan")
        assert OpenMeteoProvider().supports_location(loc) is True

    def test_country_level_key(self):
        loc = Location(raw="China", normalized="china")
        assert OpenMeteoProvider().supports_location(loc) is True


class TestGetCurrentShenzhen:
    """Replays canned fixture via mock_http conftest fixture."""

    @pytest.mark.asyncio
    async def test_get_current_shenzhen(self, mock_http):
        provider = OpenMeteoProvider()
        loc = Location(raw="Shenzhen", normalized="shenzhen")
        weather = await provider.get_current(loc)

        assert weather.temperature == 18.4
        assert weather.condition == WeatherCondition.PARTLY_CLOUDY
        assert weather.condition_raw == "wmo:2"
        assert weather.humidity == 72
        assert weather.feels_like == 17.1
        assert weather.temp_high == 22.1
        assert weather.temp_low == 14.3
        assert weather.precipitation_chance == 10
        assert weather.sunrise == "2026-01-01T06:52"
        assert weather.sunset == "2026-01-01T17:58"
        assert weather.wind_speed == 11.2
        assert weather.provider_name == "open-meteo"
        assert weather.location == "Shenzhen"
        assert weather.observed_at is not None


class TestGetForecastShenzhen:
    """Replays canned fixture via mock_http conftest fixture."""

    @pytest.mark.asyncio
    async def test_get_forecast_shenzhen(self, mock_http):
        provider = OpenMeteoProvider()
        loc = Location(raw="Shenzhen", normalized="shenzhen")
        forecast = await provider.get_forecast(loc, 1)

        assert len(forecast) == 1
        assert forecast[0].provider_name == "open-meteo"
        assert forecast[0].location == "Shenzhen"
        assert forecast[0].condition == WeatherCondition.PARTLY_CLOUDY
        assert forecast[0].condition_raw == "wmo:2"
        assert forecast[0].temp_high == 22.1
        assert forecast[0].temp_low == 14.3
        assert forecast[0].precipitation_chance == 10
        assert forecast[0].sunrise == "2026-01-01T06:52"
        assert forecast[0].sunset == "2026-01-01T17:58"
        assert forecast[0].forecast_date == date(2026, 1, 1)


class TestAliasResolution:
    def test_sz_alias_resolves_to_shenzhen(self):
        from weather.models import LOCATION_ALIASES

        assert LOCATION_ALIASES.get("sz") == "Shenzhen"
        loc = Location(raw="sz", normalized="shenzhen")
        assert OpenMeteoProvider().supports_location(loc) is True

    def test_bj_alias_resolves_to_beijing(self):
        from weather.models import LOCATION_ALIASES

        assert LOCATION_ALIASES.get("bj") == "Beijing"

    def test_sh_alias_resolves_to_shanghai(self):
        from weather.models import LOCATION_ALIASES

        assert LOCATION_ALIASES.get("sh") == "Shanghai"
