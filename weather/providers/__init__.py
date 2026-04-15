"""
Weather providers package.

Available providers:
- HKOProvider: Hong Kong Observatory (priority 1, HK only)
- BOMProvider: Australian Bureau of Meteorology (priority 6, AU only)
- MetServiceProvider: New Zealand MetService (priority 7, NZ only)
- NWSProvider: US National Weather Service (priority 7, US only)
- OpenWeatherMapProvider: Global fallback (priority 10, requires API key)
"""

from .base import (
    WeatherProvider,
    SyncWeatherProvider,
    ProviderError,
    LocationNotSupportedError,
)

from .hko import HKOProvider
from .au_bom import BOMProvider
from .nz_metservice import MetServiceProvider
from .us_nws import NWSProvider
from .openweathermap import OpenWeatherMapProvider


__all__ = [
    "WeatherProvider",
    "SyncWeatherProvider",
    "ProviderError",
    "LocationNotSupportedError",
    "HKOProvider",
    "BOMProvider",
    "MetServiceProvider",
    "NWSProvider",
    "OpenWeatherMapProvider",
]


# Lazy imports for providers
def get_hko_provider():
    """Get HK Observatory provider."""
    from .hko import HKOProvider

    return HKOProvider()


def get_openweathermap_provider(api_key: str):
    """Get OpenWeatherMap provider."""
    from .openweathermap import OpenWeatherMapProvider

    return OpenWeatherMapProvider(api_key)
