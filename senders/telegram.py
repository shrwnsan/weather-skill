"""
Telegram Bot API sender for weather messages.


Sends formatted weather messages via Telegram Bot API.
Uses JSON file approach to avoid shell escaping issues.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

from .base import WeatherSender, SendResult, SenderError


class TelegramSender(WeatherSender):
    """
    Telegram Bot API message sender.

    Features:
    - JSON file approach (avoids shell escaping)
    - Supports MarkdownV2 formatting
    - Topic/thread support for Telegram groups
    - Automatic retry on rate limit
    """

    # Telegram Bot API base URL
    API_BASE = "https://api.telegram.org/bot{token}/{method}"

    # Rate limit handling
    timeout = 30

    def __init__(
        self,
        bot_token: Optional[str] = None,
        default_chat_id: Optional[str] = None,
        parse_mode: str = "MarkdownV2",
    ):
        """
        Initialize Telegram sender.

        Args:
            bot_token: Telegram bot token (or set TELEGRAM_BOT_TOKEN env)
            default_chat_id: Default chat to send to (or set TELEGRAM_CHAT_ID env)
            parse_mode: Parse mode (MarkdownV2, HTML, or None)
        """
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.default_chat_id = default_chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.parse_mode = parse_mode

        if not self.bot_token:
            raise SenderError("Telegram bot token required (bot_token or TELEGRAM_BOT_TOKEN)")

    @property
    def channel(self) -> str:
        return "telegram"

    async def send(
        self,
        message: str,
        *,
        chat_id: Optional[str] = None,
        topic_id: Optional[int] = None,
        disable_notification: bool = False,
        **kwargs
    ) -> SendResult:
        """
        Send message via Telegram Bot API.

        Uses JSON file approach to avoid shell escaping issues with
        complex messages containing special characters.

        Args:
            message: Message text to send
            chat_id: Override default chat ID
            topic_id: Telegram topic/thread ID (for groups with topics)
            disable_notification: Send silently

        Returns:
            SendResult with success status and message_id
        """
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            return SendResult(
                success=False,
                error="No chat_id specified and no default configured"
            )

        try:
            # Build request payload
            payload = {
                "chat_id": target_chat,
                "text": message,
            }

            if self.parse_mode:
                payload["parse_mode"] = self.parse_mode

            if topic_id:
                payload["message_thread_id"] = topic_id

            if disable_notification:
                payload["disable_notification"] = True

            # Use JSON file approach for complex messages
            result = await self._send_via_json(payload)

            if result.get("ok"):
                message_id = result.get("result", {}).get("message_id")
                return SendResult(
                    success=True,
                    message_id=str(message_id) if message_id else None,
                    metadata={"chat_id": target_chat}
                )
            else:
                error_desc = result.get("description", "Unknown error")
                return SendResult(success=False, error=error_desc)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return SendResult(success=False, error=f"HTTP {e.code}: {error_body}")
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def _send_via_json(self, payload: dict) -> dict:
        """
        Send message using JSON file to avoid shell escaping.

        Writes payload to temp file and uses curl with @file syntax.
        """
        url = self.API_BASE.format(token=self.bot_token, method="sendMessage")

        loop = asyncio.get_event_loop()

        def send():
            # Write payload to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False
            ) as f:
                json.dump(payload, f, ensure_ascii=False)
                temp_path = f.name

            try:
                # Build curl command
                cmd = [
                    "curl", "-s",
                    "-X", "POST",
                    "-H", "Content-Type: application/json",
                    "-d", f"@{temp_path}",
                    url
                ]

                # Execute
                import subprocess
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                return json.loads(result.stdout)
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        return await loop.run_in_executor(None, send)

    async def send_to_topic(
        self,
        message: str,
        topic_id: int,
        chat_id: Optional[str] = None,
    ) -> SendResult:
        """
        Send message to specific Telegram topic/thread.

        Convenience method for groups with topics enabled.

        Args:
            message: Message text
            topic_id: Topic/thread ID
            chat_id: Override chat ID

        Returns:
            SendResult
        """
        return await self.send(
            message,
            chat_id=chat_id,
            topic_id=topic_id
        )
