import unittest
from unittest.mock import patch, MagicMock
from weather.models import Location, WeatherData, WeatherCondition
from weather.skill import WeatherSkill
import asyncio


class TestWeatherSkill(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.skill = WeatherSkill()

    async def test_location_normalization(self):
        from weather.models import normalize_location

        self.assertEqual(normalize_location("Hong Kong"), "Hong Kong")
        self.assertEqual(normalize_location("hong kong"), "Hong Kong")

    @patch("weather.providers.hko.HKOProvider.get_current")
    async def test_get_current_success(self, mock_get):
        mock_get.return_value = WeatherData(
            location=Location("Hong Kong"),
            temperature=25.0,
            condition=WeatherCondition.SUNNY,
        )
        result = await self.skill.get_current("Hong Kong")
        self.assertEqual(result.temperature, 25.0)
        self.assertEqual(result.location.name, "Hong Kong")


if __name__ == "__main__":
    unittest.main()
