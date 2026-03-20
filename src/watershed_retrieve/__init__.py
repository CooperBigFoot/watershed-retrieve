__version__ = "1.0.5"

from ._api import (
    available_countries,
    available_gauges,
    configure,
    get_watershed,
    get_watershed_with_rivers,
    get_watersheds,
    get_watersheds_with_rivers,
)
from ._errors import (
    ConfigurationError,
    CorruptedDataError,
    CountryNotFoundError,
    DataNotFoundError,
    DataUnavailableError,
    GaugeNotFoundError,
    InvalidArgumentError,
    R2ConnectionError,
    WatershedRetrieveError,
)
from ._types import Backend, WatershedResult

__all__ = [
    "__version__",
    "available_countries",
    "available_gauges",
    "configure",
    "get_watershed",
    "get_watershed_with_rivers",
    "get_watersheds",
    "get_watersheds_with_rivers",
    "Backend",
    "ConfigurationError",
    "CorruptedDataError",
    "CountryNotFoundError",
    "DataNotFoundError",
    "DataUnavailableError",
    "GaugeNotFoundError",
    "InvalidArgumentError",
    "R2ConnectionError",
    "WatershedRetrieveError",
    "WatershedResult",
]
