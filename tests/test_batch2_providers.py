"""Tests for Batch 2 providers (South Korea KMA, Thailand TMD)."""

import unittest
from unittest.mock import patch
from weather.models import Location, WeatherCondition
from weather.providers.kr_kma import KMAProvider
from weather.providers.th_tmd import TMDProvider


class TestKMAProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = KMAProvider(api_key="test-key")

    def test_supports_seoul(self):
        loc = Location(raw="Seoul", normalized="seoul")
        self.assertTrue(self.provider.supports_location(loc))

    def test_supports_korean_name(self):
        loc = Location(raw="서울", normalized="서울")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_without_key(self):
        provider = KMAProvider(api_key="")
        loc = Location(raw="Seoul", normalized="seoul")
        self.assertFalse(provider.supports_location(loc))

    @patch.object(KMAProvider, "_fetch_nowcast")
    async def test_get_current(self, mock_fetch):
        mock_fetch.return_value = {
            "response": {"body": {"items": {"item": [
                {"category": "T1H", "obsrValue": "22.5"},
                {"category": "REH", "obsrValue": "65"},
                {"category": "WSD", "obsrValue": "3.2"},
                {"category": "PTY", "obsrValue": "0"},
            ]}}}
        }

        loc = Location(raw="Seoul", normalized="seoul")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "Seoul")
        self.assertAlmostEqual(result.temperature, 22.5)
        self.assertEqual(result.humidity, 65)

    @patch.object(KMAProvider, "_fetch_forecast")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = {
            "response": {"body": {"items": {"item": [
                {"fcstDate": "20260415", "category": "TMX", "fcstValue": "24.0"},
                {"fcstDate": "20260415", "category": "TMN", "fcstValue": "14.0"},
                {"fcstDate": "20260415", "category": "SKY", "fcstValue": "1"},
                {"fcstDate": "20260415", "category": "PTY", "fcstValue": "0"},
                {"fcstDate": "20260415", "category": "POP", "fcstValue": "10"},
                {"fcstDate": "20260416", "category": "TMX", "fcstValue": "20.0"},
                {"fcstDate": "20260416", "category": "TMN", "fcstValue": "12.0"},
                {"fcstDate": "20260416", "category": "SKY", "fcstValue": "4"},
                {"fcstDate": "20260416", "category": "PTY", "fcstValue": "1"},
                {"fcstDate": "20260416", "category": "POP", "fcstValue": "70"},
            ]}}}
        }

        loc = Location(raw="Seoul", normalized="seoul")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].condition, WeatherCondition.SUNNY)
        self.assertEqual(result[1].condition, WeatherCondition.RAIN)
        self.assertEqual(result[0].temp_high, 24.0)
        self.assertEqual(result[1].precipitation_chance, 70)


class TestTMDProvider(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = TMDProvider(api_key="test-key")

    def test_supports_bangkok(self):
        loc = Location(raw="Bangkok", normalized="bangkok")
        self.assertTrue(self.provider.supports_location(loc))

    def test_supports_thai_name(self):
        loc = Location(raw="ภูเก็ต", normalized="ภูเก็ต")
        self.assertTrue(self.provider.supports_location(loc))

    def test_rejects_without_key(self):
        provider = TMDProvider(api_key="")
        loc = Location(raw="Bangkok", normalized="bangkok")
        self.assertFalse(provider.supports_location(loc))

    @patch.object(TMDProvider, "_fetch_observation")
    async def test_get_current(self, mock_fetch):
        mock_fetch.return_value = {
            "Stations": {"Station": [{
                "WmoStationNumber": "48455",
                "Observation": {
                    "MeanTemperature": "32.5",
                    "MeanRelativeHumidity": "72",
                    "MaxTemperature": "35.0",
                    "MinTemperature": "27.0",
                },
            }]}
        }

        loc = Location(raw="Bangkok", normalized="bangkok")
        result = await self.provider.get_current(loc)

        self.assertEqual(result.location, "Bangkok")
        self.assertAlmostEqual(result.temperature, 32.5)
        self.assertEqual(result.humidity, 72)

    @patch.object(TMDProvider, "_fetch_forecast")
    async def test_get_forecast(self, mock_fetch):
        mock_fetch.return_value = {
            "Provinces": {"Province": [{
                "ProvinceNameThai": "กรุงเทพมหานคร",
                "ForecastDaily": [
                    {
                        "Date": "15/04/2026",
                        "MaxTemperature": "35",
                        "MinTemperature": "27",
                        "WeatherDescription": "Partly Cloudy",
                        "RainChance": "10%",
                    },
                    {
                        "Date": "16/04/2026",
                        "MaxTemperature": "33",
                        "MinTemperature": "26",
                        "WeatherDescription": "Thunder Storm",
                        "RainChance": "60%",
                    },
                ]
            }]}
        }

        loc = Location(raw="Bangkok", normalized="bangkok")
        result = await self.provider.get_forecast(loc, days=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].condition, WeatherCondition.PARTLY_CLOUDY)
        self.assertEqual(result[1].condition, WeatherCondition.THUNDERSTORM)
        self.assertEqual(result[0].temp_high, 35.0)
        self.assertEqual(result[1].precipitation_chance, 60)


if __name__ == "__main__":
    unittest.main()
