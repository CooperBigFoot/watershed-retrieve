__version__ = "1.0.0"

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
    CountryNotFoundError,
    DataNotFoundError,
    DataUnavailableError,
    GaugeNotFoundError,
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
    "CountryNotFoundError",
    "DataNotFoundError",
    "DataUnavailableError",
    "GaugeNotFoundError",
    "R2ConnectionError",
    "WatershedRetrieveError",
    "WatershedResult",
]
