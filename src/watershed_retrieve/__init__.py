__version__ = "0.1.2"

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
    GaugeNotFoundError,
    WatershedRetrieveError,
)
from ._types import WatershedResult

__all__ = [
    "__version__",
    "available_countries",
    "available_gauges",
    "configure",
    "get_watershed",
    "get_watershed_with_rivers",
    "get_watersheds",
    "get_watersheds_with_rivers",
    "CountryNotFoundError",
    "DataNotFoundError",
    "GaugeNotFoundError",
    "WatershedRetrieveError",
    "WatershedResult",
]
