"""Tests for Batch 1 providers (Indonesia BMKG, Germany DWD/Bright Sky)."""

import unittest
from unittest.mock import patch
from weather.models import Location, WeatherCondition
from weather.providers.id_bmkg import BMKGProvider
from weather.providers.de_dwd import DWDProvider


class TestBMKGProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = BMKGProvider()

    def test_supports_jakarta(self):
        loc = Location(raw="Jakarta", normalized="jakarta")
        self.assertTrue(self.provider.supports_location(loc))

    def test_supports_bali(self):
        loc = Location(raw="Bali", normalized="bali")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_non_indonesia(self):
        loc = Location(raw="Tokyo", normalized="tokyo")
        self.assertFalse(self.provider.supports_location(loc))

    @patch.object(BMKGProvider, "_fetch_forecast")
    async def test_get_current(self, mock_fetch):
        mock_fetch.return_value = {
            "lokasi": {
                "kotkab": "Kota Jakarta Pusat",
                "provinsi": "DKI Jakarta",
            },
            "data": [{
                "cuaca": [[
                    {
                        "utc_datetime": "2026-04-15 05:00:00",
                        "local_datetime": "2026-04-15 12:00:00",
                        "t": 32,
                        "hu": 75,
                        "weather_desc_en": "Partly Cloudy",
                        "ws": 15,
                        "wd": "S",
                        "tcc": 50,
                        "vs_text": "> 10 km",
                    },
                ]]
            }]
        }

        loc = Location(raw="Jakarta", normalized="jakarta")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "Kota Jakarta Pusat")
        self.assertEqual(result.temperature, 32.0)
        self.assertEqual(result.condition, WeatherCondition.PARTLY_CLOUDY)
        self.assertEqual(result.humidity, 75)

    @patch.object(BMKGProvider, "_fetch_forecast")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = {
            "lokasi": {"kotkab": "Denpasar", "provinsi": "Bali"},
            "data": [{
                "cuaca": [
                    [
                        {
                            "utc_datetime": "2026-04-15 05:00:00",
                            "local_datetime": "2026-04-15 12:00:00",
                            "t": 30,
                            "hu": 80,
                            "weather_desc_en": "Thunderstorm",
                            "ws": 20,
                            "wd": "SW",
                        },
                    ],
                    [
                        {
                            "utc_datetime": "2026-04-16 05:00:00",
                            "local_datetime": "2026-04-16 12:00:00",
                            "t": 31,
                            "hu": 70,
                            "weather_desc_en": "Partly Cloudy",
                            "ws": 12,
                            "wd": "S",
                        },
                    ],
                ]
            }]
        }

        loc = Location(raw="Bali", normalized="bali")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].condition, WeatherCondition.THUNDERSTORM)
        self.assertEqual(result[1].condition, WeatherCondition.PARTLY_CLOUDY)


class TestDWDProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = DWDProvider()

    def test_supports_berlin(self):
        loc = Location(raw="Berlin", normalized="berlin")
        self.assertTrue(self.provider.supports_location(loc))

    def test_supports_german_name(self):
        loc = Location(raw="München", normalized="münchen")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_non_germany(self):
        loc = Location(raw="Paris", normalized="paris")
        self.assertFalse(self.provider.supports_location(loc))

    @patch.object(DWDProvider, "_fetch_current")
    async def test_get_current(self, mock_fetch):
        mock_fetch.return_value = {
            "weather": {
                "timestamp": "2026-04-15T12:00:00+00:00",
                "temperature": 18.5,
                "relative_humidity": 62,
                "wind_speed_10": 12.3,
                "wind_direction_10": 270,
                "icon": "partly-cloudy-day",
                "visibility": 25000,
                "pressure_msl": 1013.2,
                "sunshine": 45,
            }
        }

        loc = Location(raw="Berlin", normalized="berlin")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "Berlin")
        self.assertAlmostEqual(result.temperature, 18.5)
        self.assertEqual(result.condition, WeatherCondition.PARTLY_CLOUDY)
        self.assertEqual(result.humidity, 62)
        self.assertAlmostEqual(result.wind_speed, 12.3)

    @patch.object(DWDProvider, "_fetch_weather")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = {
            "weather": [
                {
                    "timestamp": "2026-04-15T06:00:00+00:00",
                    "temperature": 10.0,
                    "relative_humidity": 80,
                    "wind_speed_10": 8.0,
                    "precipitation": 0.0,
                    "icon": "cloudy",
                },
                {
                    "timestamp": "2026-04-15T12:00:00+00:00",
                    "temperature": 18.0,
                    "relative_humidity": 55,
                    "wind_speed_10": 15.0,
                    "precipitation": 0.0,
                    "icon": "partly-cloudy-day",
                },
                {
                    "timestamp": "2026-04-16T06:00:00+00:00",
                    "temperature": 8.0,
                    "relative_humidity": 85,
                    "wind_speed_10": 10.0,
                    "precipitation": 2.5,
                    "icon": "rain",
                },
                {
                    "timestamp": "2026-04-16T12:00:00+00:00",
                    "temperature": 14.0,
                    "relative_humidity": 70,
                    "wind_speed_10": 12.0,
                    "precipitation": 1.0,
                    "icon": "rain",
                },
            ]
        }

        loc = Location(raw="Berlin", normalized="berlin")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        # Day 1: partly-cloudy-day is less severe than cloudy, but cloudy has higher severity
        self.assertIn(result[0].condition, [WeatherCondition.CLOUDY, WeatherCondition.PARTLY_CLOUDY])
        # Day 2: rain both entries
        self.assertEqual(result[1].condition, WeatherCondition.RAIN)
        self.assertEqual(result[0].temp_high, 18.0)
        self.assertEqual(result[0].temp_low, 10.0)


if __name__ == "__main__":
    unittest.main()
