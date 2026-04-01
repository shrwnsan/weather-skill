"""
Weather providers package.

Available providers:
- HKOProvider: Hong Kong Observatory (priority 1, HK only)
- SGNEAProvider: Singapore NEA (priority 2, Singapore only)
- JMAProvider: Japan Meteorological Agency (priority 3, Japan only)
- CWAProvider: Taiwan Central Weather Administration (priority 4, Taiwan only)
- UKMetOfficeProvider: UK Met Office (priority 5, UK only)
- BOMProvider: Australian Bureau of Meteorology (priority 6, AU only)
- MetServiceProvider: New Zealand MetService (priority 7, NZ only)
- NWSProvider: US National Weather Service (priority 7, US only)
- OpenWeatherMapProvider: Global fallback (priority 10, requires API key)
"""

from .base import WeatherProvider, SyncWeatherProvider, ProviderError, LocationNotSupportedError

from .hko import HKOProvider
from .sg_nea import SGNEAProvider
from .jma import JMAProvider
from .tw_cwa import CWAProvider
from .uk_metoffice import UKMetOfficeProvider
from .au_bom import BOMProvider
from .nz_metservice import MetServiceProvider
from .us_nws import NWSProvider
from .openweathermap import OpenWeatherMapProvider

from ..models import LOCATION_ALIASES

LOCATION_ALIASES.update({
    # Japan
    "jp": "Japan",
    "japan": "Japan",
    "日本": "Japan",
    "tokyo": "Tokyo",
    "東京": "Tokyo",
    "osaka": "Osaka",
    "大阪": "Osaka",
    "yokohama": "Yokohama",
    "横浜": "Yokohama",
    "kyoto": "Kyoto",
    "京都": "Kyoto",
    "nagoya": "Nagoya",
    "名古屋": "Nagoya",
    "sapporo": "Sapporo",
    "札幌": "Sapporo",
    "fukuoka": "Fukuoka",
    "福岡": "Fukuoka",
    "hiroshima": "Hiroshima",
    "広島": "Hiroshima",
    "sendai": "Sendai",
    "仙台": "Sendai",
    "naha": "Naha",
    "那覇": "Naha",
})

__all__ = [
    "WeatherProvider",
    "SyncWeatherProvider",
    "ProviderError",
    "LocationNotSupportedError",
    "HKOProvider",
    "SGNEAProvider",
    "JMAProvider",
    "CWAProvider",
    "UKMetOfficeProvider",
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

def get_sgnea_provider():
    """Get Singapore NEA provider."""
    from .sg_nea import SGNEAProvider
    return SGNEAProvider()

def get_jma_provider():
    """Get Japan Meteorological Agency provider."""
    from .jma import JMAProvider
    return JMAProvider()

def get_cwa_provider(api_key: str):
    """Get Taiwan CWA provider."""
    from .tw_cwa import CWAProvider
    return CWAProvider(api_key)

def get_openweathermap_provider(api_key: str):
    """Get OpenWeatherMap provider."""
    from .openweathermap import OpenWeatherMapProvider
    return OpenWeatherMapProvider(api_key)
