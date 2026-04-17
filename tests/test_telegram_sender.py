"""Tests for TelegramSender security."""

import asyncio
import inspect
import json
import unittest
from unittest.mock import patch, MagicMock

from weather.senders.telegram import TelegramSender
from weather.senders.base import SendResult


class TestTelegramSenderSecurity(unittest.IsolatedAsyncioTestCase):
    """Verify TelegramSender uses safe HTTP patterns only."""

    def test_no_subprocess_import(self):
        """Source must not import subprocess."""
        import weather.senders.telegram as mod
        source = inspect.getsource(mod)
        self.assertNotIn("subprocess", source)

    def test_no_curl_usage(self):
        """Source must not use curl."""
        import weather.senders.telegram as mod
        source = inspect.getsource(mod)
        self.assertNotIn("curl", source)

    async def test_send_uses_urllib(self):
        """Send works correctly with mocked urllib.request.urlopen."""
        sender = TelegramSender(
            bot_token="test-token",
            default_chat_id="12345",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "ok": True,
            "result": {"message_id": 42},
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await sender.send("Hello, world!")

        self.assertIsInstance(result, SendResult)
        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "42")


if __name__ == "__main__":
    unittest.main()
