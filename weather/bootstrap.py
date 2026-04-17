"""
Bootstrap factory for WeatherSkill.

Builds a fully-configured WeatherSkill instance with all available
providers, formatters, and senders registered based on environment
configuration.
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .skill import WeatherSkill


def build_default_skill(**overrides) -> "WeatherSkill":
    """
    Build a fully-configured WeatherSkill instance.

    Registers all available providers, formatters, and senders
    based on environment variables. Accepts optional overrides
    for testing or custom configuration.

    Args:
        **overrides: Optional overrides for testing:
            - providers: list[WeatherProvider] -- override default providers
            - formatters: dict[str, WeatherFormatter] -- override default formatters
            - senders: dict[str, WeatherSender] -- override default senders

    Returns:
        Configured WeatherSkill instance
    """
    from .skill import WeatherSkill

    if "providers" not in overrides:
        providers = _build_providers()
    else:
        providers = overrides.pop("providers")

    if "formatters" not in overrides:
        formatters = _build_formatters()
    else:
        formatters = overrides.pop("formatters")

    if "senders" not in overrides:
        senders = _build_senders()
    else:
        senders = overrides.pop("senders")

    return WeatherSkill(
        providers=providers,
        formatters=formatters,
        senders=senders,
    )


def _build_providers():
    """Build the default provider list from environment."""
    from .providers.base import WeatherProvider

    providers: list[WeatherProvider] = []

    # Free providers (no API key required)
    try:
        from .providers.hko import HKOProvider
        providers.append(HKOProvider())
    except ImportError:
        pass

    try:
        from .providers.sg_nea import SGNEAProvider
        providers.append(SGNEAProvider())
    except ImportError:
        pass

    try:
        from .providers.jma import JMAProvider
        providers.append(JMAProvider())
    except ImportError:
        pass

    try:
        from .providers.au_bom import BOMProvider
        providers.append(BOMProvider())
    except ImportError:
        pass

    try:
        from .providers.nz_metservice import MetServiceProvider
        providers.append(MetServiceProvider())
    except ImportError:
        pass

    try:
        from .providers.us_nws import NWSProvider
        providers.append(NWSProvider())
    except ImportError:
        pass

    try:
        from .providers.id_bmkg import BMKGProvider
        providers.append(BMKGProvider())
    except ImportError:
        pass

    try:
        from .providers.de_dwd import DWDProvider
        providers.append(DWDProvider())
    except ImportError:
        pass

    # Key-required providers (only when env var is set)
    if os.environ.get("CWA_API_KEY"):
        try:
            from .providers.tw_cwa import CWAProvider
            providers.append(CWAProvider())
        except ImportError:
            pass

    if os.environ.get("METOFFICE_API_KEY"):
        try:
            from .providers.uk_metoffice import UKMetOfficeProvider
            providers.append(UKMetOfficeProvider())
        except ImportError:
            pass

    if os.environ.get("KMA_SERVICE_KEY"):
        try:
            from .providers.kr_kma import KMAProvider
            providers.append(KMAProvider())
        except ImportError:
            pass

    if os.environ.get("TMD_API_TOKEN"):
        try:
            from .providers.th_tmd import TMDProvider
            providers.append(TMDProvider())
        except ImportError:
            pass

    owm_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if owm_key:
        try:
            from .providers.openweathermap import OpenWeatherMapProvider
            providers.append(OpenWeatherMapProvider(api_key=owm_key))
        except ImportError:
            pass

    return providers


def _build_formatters():
    """Build the default formatter dict."""
    formatters = {}

    try:
        from .formatters.cli_text import CliTextFormatter
        formatters["text"] = CliTextFormatter()
    except ImportError:
        pass

    try:
        from .formatters.telegram import TelegramFormatter
        formatters["telegram"] = TelegramFormatter()
    except ImportError:
        pass

    try:
        from .formatters.whatsapp import WhatsAppFormatter
        formatters["whatsapp"] = WhatsAppFormatter()
    except ImportError:
        pass

    return formatters


def _build_senders():
    """Build the default sender dict from environment."""
    senders = {}

    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        try:
            from .senders.telegram import TelegramSender
            senders["telegram"] = TelegramSender()
        except ImportError:
            pass

    return senders
