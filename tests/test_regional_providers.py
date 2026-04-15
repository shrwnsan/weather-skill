"""Tests for regional weather providers (SG NEA, JMA, CWA, UK Met Office)."""

import unittest
from unittest.mock import patch, AsyncMock
from weather.models import Location, WeatherData, WeatherCondition
from weather.providers.sg_nea import SGNEAProvider
from weather.providers.jma import JMAProvider
from weather.providers.tw_cwa import CWAProvider
from weather.providers.uk_metoffice import UKMetOfficeProvider


class TestSGNEAProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = SGNEAProvider()

    def test_supports_singapore(self):
        loc = Location(raw="Singapore", normalized="singapore")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_non_singapore(self):
        loc = Location(raw="Tokyo", normalized="tokyo")
        self.assertFalse(self.provider.supports_location(loc))

    @patch.object(SGNEAProvider, "_fetch_json")
    async def test_get_current(self, mock_fetch):
        mock_fetch.side_effect = [
            # Temperature
            {"data": {"readings": [{"data": [
                {"value": 30.0}, {"value": 31.0}, {"value": 29.0}
            ]}]}},
            # Humidity
            {"data": {"readings": [{"data": [
                {"value": 80}, {"value": 85}
            ]}]}},
            # 24h forecast
            {"data": {"records": [{"general": {
                "forecast": "Thundery Showers",
                "temperature": {"high": 33, "low": 25},
                "relativeHumidity": {"high": 95, "low": 60},
                "wind": {"direction": "SW", "speed": {"low": 10, "high": 20}},
            }}]}},
            # PSI
            {"data": {"readings": [{"data": {
                "psi_twenty_four_hourly": {"national": 42}
            }}]}},
        ]

        loc = Location(raw="Singapore", normalized="singapore")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "Singapore")
        self.assertAlmostEqual(result.temperature, 30.0, places=0)
        self.assertEqual(result.condition, WeatherCondition.THUNDERSTORM)
        self.assertEqual(result.aqi, 42)

    @patch.object(SGNEAProvider, "_fetch_json")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = {
            "data": {"records": [{"forecasts": [
                {
                    "date": "2026-04-15",
                    "forecast": "Partly Cloudy",
                    "temperature": {"high": 33, "low": 26},
                    "relativeHumidity": {"high": 90, "low": 60},
                    "wind": {"direction": "S", "speed": {"low": 10, "high": 15}},
                },
                {
                    "date": "2026-04-16",
                    "forecast": "Showers",
                    "temperature": {"high": 31, "low": 25},
                    "relativeHumidity": {"high": 95, "low": 65},
                    "wind": {"direction": "SW", "speed": {"low": 10, "high": 20}},
                },
            ]}]}
        }

        loc = Location(raw="Singapore", normalized="singapore")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].condition, WeatherCondition.PARTLY_CLOUDY)
        self.assertEqual(result[1].condition, WeatherCondition.SHOWERS)


class TestJMAProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = JMAProvider()

    def test_supports_tokyo(self):
        loc = Location(raw="Tokyo", normalized="tokyo")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_non_japan(self):
        loc = Location(raw="London", normalized="london")
        self.assertFalse(self.provider.supports_location(loc))

    @patch.object(JMAProvider, "_fetch_overview")
    @patch.object(JMAProvider, "_fetch_forecast")
    async def test_get_current(self, mock_forecast, mock_overview):
        mock_forecast.return_value = [{
            "timeSeries": [
                {
                    "timeDefines": ["2026-04-15T05:00:00+09:00"],
                    "areas": [{"weatherCodes": ["100"], "weathers": ["晴れ"]}],
                },
                {
                    "timeDefines": ["2026-04-15T06:00:00+09:00"],
                    "areas": [{"pops": ["10", "20", "30"]}],
                },
                {
                    "timeDefines": ["2026-04-15T09:00:00+09:00"],
                    "areas": [{"temps": ["12", "22"]}],
                },
            ]
        }]
        mock_overview.return_value = {
            "text": "東京地方は、高気圧に覆われて晴れています。"
        }

        loc = Location(raw="Tokyo", normalized="tokyo")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "Tokyo")
        self.assertEqual(result.condition, WeatherCondition.SUNNY)
        self.assertEqual(result.temp_high, 22.0)
        self.assertEqual(result.temp_low, 12.0)
        self.assertEqual(result.precipitation_chance, 30)

    @patch.object(JMAProvider, "_fetch_forecast")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = [
            {},  # short-term (index 0)
            {    # weekly (index 1)
                "timeSeries": [
                    {
                        "timeDefines": [
                            "2026-04-15T00:00:00+09:00",
                            "2026-04-16T00:00:00+09:00",
                        ],
                        "areas": [{
                            "weatherCodes": ["100", "200"],
                            "pops": ["10", "40"],
                        }],
                    },
                    {
                        "timeDefines": [
                            "2026-04-15T00:00:00+09:00",
                            "2026-04-16T00:00:00+09:00",
                        ],
                        "areas": [{
                            "tempsMin": ["10", "12"],
                            "tempsMax": ["20", "18"],
                        }],
                    },
                ]
            },
        ]

        loc = Location(raw="Tokyo", normalized="tokyo")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].condition, WeatherCondition.SUNNY)
        self.assertEqual(result[1].condition, WeatherCondition.CLOUDY)
        self.assertEqual(result[0].temp_high, 20.0)


class TestCWAProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = CWAProvider(api_key="test-key")

    def test_supports_taipei(self):
        loc = Location(raw="Taipei", normalized="taipei")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_without_key(self):
        provider = CWAProvider(api_key="")
        loc = Location(raw="Taipei", normalized="taipei")
        self.assertFalse(provider.supports_location(loc))

    @patch.object(CWAProvider, "_fetch_api")
    async def test_get_current(self, mock_fetch):
        mock_fetch.side_effect = [
            # Observations
            {"records": {"Station": [{
                "WeatherElement": {
                    "AirTemperature": 28.5,
                    "RelativeHumidity": 75,
                    "WindSpeed": 3.2,
                    "WindDirection": 180,
                },
                "ObsTime": {"DateTime": "2026-04-15T10:00:00+08:00"},
            }]}},
            # 36h forecast
            {"records": {"location": [{
                "weatherElement": [
                    {
                        "elementName": "Wx",
                        "time": [{"parameter": {"parameterName": "多雲時晴"}}],
                    },
                    {
                        "elementName": "PoP",
                        "time": [{"parameter": {"parameterName": "20"}}],
                    },
                ]
            }]}},
        ]

        loc = Location(raw="Taipei", normalized="taipei")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.temperature, 28.5)
        self.assertEqual(result.condition, WeatherCondition.PARTLY_CLOUDY)
        self.assertEqual(result.precipitation_chance, 20)


class TestUKMetOfficeProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = UKMetOfficeProvider(api_key="test-key")

    def test_supports_london(self):
        loc = Location(raw="London", normalized="london")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_without_key(self):
        provider = UKMetOfficeProvider(api_key="")
        loc = Location(raw="London", normalized="london")
        self.assertFalse(provider.supports_location(loc))

    @patch.object(UKMetOfficeProvider, "_fetch_hourly")
    async def test_get_current(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [{
                "properties": {
                    "timeSeries": [{
                        "time": "2026-04-15T12:00:00Z",
                        "screenTemperature": 15.2,
                        "feelsLikeTemperature": 13.0,
                        "screenRelativeHumidity": 65.3,
                        "windSpeed10m": 5.0,
                        "windDirectionFrom10m": 225,
                        "significantWeatherCode": 3,
                        "visibility": 20000,
                        "uvIndex": 4,
                        "probOfPrecipitation": 15,
                    }]
                }
            }]
        }

        loc = Location(raw="London", normalized="london")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "London")
        self.assertAlmostEqual(result.temperature, 15.2)
        self.assertEqual(result.condition, WeatherCondition.PARTLY_CLOUDY)
        self.assertEqual(result.humidity, 65)
        self.assertAlmostEqual(result.wind_speed, 18.0, places=0)

    @patch.object(UKMetOfficeProvider, "_fetch_daily")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [{
                "properties": {
                    "timeSeries": [
                        {
                            "time": "2026-04-15T00:00:00Z",
                            "dayMaxScreenTemperature": 16.0,
                            "nightMinScreenTemperature": 8.0,
                            "daySignificantWeatherCode": 1,
                            "dayProbabilityOfPrecipitation": 5,
                            "maxUvIndex": 5,
                            "midday10MWindSpeed": 4.0,
                            "midday10MWindDirection": 180,
                            "middayRelativeHumidity": 60,
                        },
                        {
                            "time": "2026-04-16T00:00:00Z",
                            "dayMaxScreenTemperature": 14.0,
                            "nightMinScreenTemperature": 7.0,
                            "daySignificantWeatherCode": 15,
                            "dayProbabilityOfPrecipitation": 80,
                            "maxUvIndex": 2,
                            "midday10MWindSpeed": 6.0,
                            "midday10MWindDirection": 270,
                            "middayRelativeHumidity": 85,
                        },
                    ]
                }
            }]
        }

        loc = Location(raw="London", normalized="london")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].condition, WeatherCondition.SUNNY)
        self.assertEqual(result[1].condition, WeatherCondition.HEAVY_RAIN)
        self.assertEqual(result[0].temp_high, 16.0)


if __name__ == "__main__":
    unittest.main()
