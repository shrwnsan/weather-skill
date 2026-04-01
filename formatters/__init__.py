"""
Weather formatters package.

Available formatters:
- TelegramFormatter: Telegram MarkdownV2 format
- WhatsAppFormatter: WhatsApp formatting (*bold*, _italic_)
"""

from .base import WeatherFormatter, FormatterError
from .telegram import TelegramFormatter
from .whatsapp import WhatsAppFormatter

__all__ = [
    "WeatherFormatter",
    "FormatterError",
    "TelegramFormatter",
    "WhatsAppFormatter",
]

def get_telegram_formatter():
    """Get Telegram MarkdownV2 formatter."""
    return TelegramFormatter()

def get_whatsapp_formatter():
    """Get WhatsApp formatter."""
    return WhatsAppFormatter()
