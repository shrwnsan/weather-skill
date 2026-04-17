"""Tests for bootstrap.build_default_skill()."""

import os
import unittest
from unittest.mock import patch


class TestBuildDefaultSkill(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_free_providers_always_registered(self):
        """All 8 free providers present when no API keys set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        expected_free = {"hko", "sg_nea", "jma", "bom", "metservice", "nws", "bmkg", "dwd"}
        self.assertTrue(expected_free.issubset(names), f"Missing free providers. Got: {names}")

    @patch.dict(os.environ, {}, clear=True)
    def test_formatters_registered(self):
        """text, telegram, whatsapp formatters present."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        for fmt in ("text", "telegram", "whatsapp"):
            self.assertIn(fmt, skill.platforms, f"Missing formatter: {fmt}")

    @patch.dict(os.environ, {"OPENWEATHERMAP_API_KEY": "test-key"}, clear=True)
    def test_owm_registered_with_key(self):
        """OWM provider registered when API key is set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        self.assertIn("openweathermap", names)

    @patch.dict(os.environ, {}, clear=True)
    def test_owm_absent_without_key(self):
        """OWM provider absent when no API key."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        self.assertNotIn("openweathermap", names)

    @patch.dict(os.environ, {"CWA_API_KEY": "test-key"}, clear=True)
    def test_cwa_registered_with_key(self):
        """CWA provider registered when API key is set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        self.assertIn("cwa", names)

    @patch.dict(os.environ, {"METOFFICE_API_KEY": "test-key"}, clear=True)
    def test_metoffice_registered_with_key(self):
        """UK Met Office provider registered when API key is set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        self.assertIn("metoffice", names)

    @patch.dict(os.environ, {"KMA_SERVICE_KEY": "test-key"}, clear=True)
    def test_kma_registered_with_key(self):
        """KMA provider registered when service key is set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        self.assertIn("kma", names)

    @patch.dict(os.environ, {"TMD_API_TOKEN": "test-token"}, clear=True)
    def test_tmd_registered_with_key(self):
        """TMD provider registered when API token is set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        names = {p.name for p in skill.providers}
        self.assertIn("tmd", names)

    @patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test-token"}, clear=True)
    def test_telegram_sender_registered_with_token(self):
        """Telegram sender registered when bot token is set."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        self.assertIn("telegram", skill.channels)

    @patch.dict(os.environ, {}, clear=True)
    def test_telegram_sender_absent_without_token(self):
        """Telegram sender absent when no bot token."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        self.assertNotIn("telegram", skill.channels)

    @patch.dict(os.environ, {}, clear=True)
    def test_providers_sorted_by_priority(self):
        """Providers are sorted by priority (lower number = higher priority)."""
        from weather.bootstrap import build_default_skill
        skill = build_default_skill()

        priorities = [p.priority for p in skill.providers]
        self.assertEqual(priorities, sorted(priorities))


if __name__ == "__main__":
    unittest.main()
