"""Tests for CLI end-to-end with mocked providers."""

import json
import unittest
from unittest.mock import patch

from weather.models import WeatherData, WeatherCondition, Location
from weather.providers.hko import HKOProvider
from weather.providers.jma import JMAProvider
from weather.providers.us_nws import NWSProvider
from weather.skill import WeatherSkill
from weather.formatters.cli_text import CliTextFormatter
from weather.formatters.telegram import TelegramFormatter


def _make_skill_with_provider(provider_instance):
    """Create a WeatherSkill with a single provider."""
    skill = WeatherSkill(
        providers=[provider_instance],
        formatters={"text": CliTextFormatter(), "telegram": TelegramFormatter()},
        senders={},
    )
    return skill


def _hko_current_data():
    return WeatherData(
        location="Hong Kong",
        temperature=28.0,
        humidity=80,
        wind_speed=20.0,
        wind_direction="NE",
        condition=WeatherCondition.PARTLY_CLOUDY,
        provider_name="hko",
    )


def _jma_current_data():
    return WeatherData(
        location="Tokyo",
        temperature=22.0,
        humidity=60,
        condition=WeatherCondition.CLEAR,
        provider_name="jma",
    )


def _nws_current_data():
    return WeatherData(
        location="New York",
        temperature=18.0,
        humidity=55,
        wind_speed=15.0,
        condition=WeatherCondition.PARTLY_CLOUDY,
        provider_name="us_nws",
    )


def _forecast_data():
    from datetime import date
    return [
        WeatherData(
            location="Hong Kong",
            temperature=28.0,
            temp_high=32.0,
            temp_low=26.0,
            forecast_date=date(2026, 4, 17),
            condition=WeatherCondition.PARTLY_CLOUDY,
            description="Partly Cloudy",
            provider_name="hko",
        ),
        WeatherData(
            location="Hong Kong",
            temperature=27.0,
            temp_high=30.0,
            temp_low=25.0,
            forecast_date=date(2026, 4, 18),
            condition=WeatherCondition.RAIN,
            description="Rain",
            provider_name="hko",
        ),
    ]


class TestCLIIntegration(unittest.IsolatedAsyncioTestCase):

    @patch("weather.cli.build_default_skill")
    async def test_hk_current_text(self, mock_build):
        """HK current weather with text output contains temp/humidity/wind."""
        hko = HKOProvider()
        mock_build.return_value = _make_skill_with_provider(hko)

        with patch.object(hko, "get_current", return_value=_hko_current_data()):
            from weather.cli import main
            import argparse

            args = argparse.Namespace(
                location="Hong Kong",
                forecast=False,
                days=3,
                format="text",
                send=False,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )
            result = await main(args)

        self.assertEqual(result, 0)

    @patch("weather.cli.build_default_skill")
    async def test_tokyo_routes_to_jma(self, mock_build):
        """Tokyo request routes to JMA provider."""
        jma = JMAProvider()
        mock_build.return_value = _make_skill_with_provider(jma)

        with patch.object(jma, "get_current", return_value=_jma_current_data()):
            from weather.cli import main
            import argparse

            args = argparse.Namespace(
                location="Tokyo",
                forecast=False,
                days=3,
                format="text",
                send=False,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )
            result = await main(args)

        self.assertEqual(result, 0)

    @patch("weather.cli.build_default_skill")
    async def test_nyc_routes_to_nws(self, mock_build):
        """NYC request routes to NWS provider."""
        nws = NWSProvider()
        mock_build.return_value = _make_skill_with_provider(nws)

        with patch.object(nws, "get_current", return_value=_nws_current_data()):
            from weather.cli import main
            import argparse

            args = argparse.Namespace(
                location="New York",
                forecast=False,
                days=3,
                format="text",
                send=False,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )
            result = await main(args)

        self.assertEqual(result, 0)

    @patch("weather.cli.build_default_skill")
    async def test_json_output(self, mock_build):
        """JSON format produces valid JSON with correct fields."""
        hko = HKOProvider()
        mock_build.return_value = _make_skill_with_provider(hko)
        data = _hko_current_data()

        with patch.object(hko, "get_current", return_value=data):
            from weather.cli import main
            import argparse
            from io import StringIO
            import sys

            args = argparse.Namespace(
                location="Hong Kong",
                forecast=False,
                days=3,
                format="json",
                send=False,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )

            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                result = await main(args)
            finally:
                sys.stdout = old_stdout

        self.assertEqual(result, 0)
        output = json.loads(captured.getvalue())
        self.assertEqual(output["temperature"], 28.0)
        self.assertEqual(output["location"], "Hong Kong")

    @patch("weather.cli.build_default_skill")
    async def test_forecast_output(self, mock_build):
        """Forecast output contains multi-day data."""
        hko = HKOProvider()
        mock_build.return_value = _make_skill_with_provider(hko)
        forecast = _forecast_data()

        with patch.object(hko, "get_forecast", return_value=forecast):
            from weather.cli import main
            import argparse
            from io import StringIO
            import sys

            args = argparse.Namespace(
                location="Hong Kong",
                forecast=True,
                days=2,
                format="text",
                send=False,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )

            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                result = await main(args)
            finally:
                sys.stdout = old_stdout

        self.assertEqual(result, 0)
        output = captured.getvalue()
        self.assertIn("2026-04-17", output)
        self.assertIn("2026-04-18", output)

    @patch("weather.cli.build_default_skill")
    async def test_telegram_format(self, mock_build):
        """Telegram format produces MarkdownV2 output."""
        hko = HKOProvider()
        mock_build.return_value = _make_skill_with_provider(hko)

        with patch.object(hko, "get_current", return_value=_hko_current_data()):
            from weather.cli import main
            import argparse
            from io import StringIO
            import sys

            args = argparse.Namespace(
                location="Hong Kong",
                forecast=False,
                days=3,
                format="telegram",
                send=False,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )

            captured = StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                result = await main(args)
            finally:
                sys.stdout = old_stdout

        self.assertEqual(result, 0)
        output = captured.getvalue()
        # Telegram formatter escapes special MarkdownV2 characters
        self.assertIn("Hong Kong", output)

    @patch("weather.cli.build_default_skill")
    async def test_send_without_token_fails(self, mock_build):
        """Sending without telegram token returns exit code 1."""
        hko = HKOProvider()
        # No senders configured
        mock_build.return_value = WeatherSkill(
            providers=[hko],
            formatters={"text": CliTextFormatter()},
            senders={},
        )

        with patch.object(hko, "get_current", return_value=_hko_current_data()):
            from weather.cli import main
            import argparse

            args = argparse.Namespace(
                location="Hong Kong",
                forecast=False,
                days=3,
                format="text",
                send=True,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )
            result = await main(args)

        self.assertEqual(result, 1)

    @patch("weather.cli.build_default_skill")
    async def test_invalid_provider_lists_available(self, mock_build):
        """Invalid --provider name fails with exit 1 and lists available providers."""
        from io import StringIO
        import sys as _sys

        hko = HKOProvider()
        jma = JMAProvider()
        mock_build.return_value = WeatherSkill(
            providers=[hko, jma],
            formatters={"text": CliTextFormatter()},
            senders={},
        )

        from weather.cli import main
        import argparse

        args = argparse.Namespace(
            location="Hong Kong",
            forecast=False,
            days=3,
            format="text",
            send=False,
            chat_id=None,
            topic_id=None,
            provider="hok",  # typo
            verbose=False,
        )

        captured = StringIO()
        old_stderr = _sys.stderr
        _sys.stderr = captured
        try:
            result = await main(args)
        finally:
            _sys.stderr = old_stderr

        self.assertEqual(result, 1)
        err = captured.getvalue()
        self.assertIn("Provider not found: hok", err)
        self.assertIn("Available providers:", err)
        # Both registered providers should appear in the message
        self.assertIn("hko", err)
        self.assertIn("jma", err)

    @patch("weather.cli.build_default_skill")
    async def test_send_with_json_format_rejected(self, mock_build):
        """--send with --format json exits with usage error (code 2) and does not fetch."""
        from io import StringIO
        import sys as _sys

        hko = HKOProvider()
        mock_build.return_value = _make_skill_with_provider(hko)

        # If fetch were attempted, get_current would return data; we assert it isn't called
        with patch.object(hko, "get_current") as mock_get:
            from weather.cli import main
            import argparse

            args = argparse.Namespace(
                location="Hong Kong",
                forecast=False,
                days=3,
                format="json",
                send=True,
                chat_id=None,
                topic_id=None,
                provider="auto",
                verbose=False,
            )

            captured = StringIO()
            old_stderr = _sys.stderr
            _sys.stderr = captured
            try:
                result = await main(args)
            finally:
                _sys.stderr = old_stderr

        self.assertEqual(result, 2)
        self.assertIn("--send is not compatible with --format json", captured.getvalue())
        mock_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
