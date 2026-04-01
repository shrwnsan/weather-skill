"""
Weather formatters package.

Available formatters:
- TelegramFormatter: Telegram MarkdownV2 format
- WhatsAppFormatter: WhatsApp formatting (future)
"""

from .base import WeatherFormatter, FormatterError
from .telegram import TelegramFormatter

__all__ = [
    "WeatherFormatter",
    "FormatterError",
    "TelegramFormatter",
]

def get_telegram_formatter():
    """Get Telegram MarkdownV2 formatter."""
    return TelegramFormatter()
