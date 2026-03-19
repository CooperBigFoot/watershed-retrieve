class WatershedRetrieveError(Exception):
    pass


class CountryNotFoundError(WatershedRetrieveError):
    pass
    # Message format: "Country 'atlantis' not supported. Available: australia, brazil, ..."


class GaugeNotFoundError(WatershedRetrieveError):
    pass
    # Message format: "Gauge '99Z/99Z' not found in 'portugal'. Use available_gauges('portugal')..."


class DataNotFoundError(WatershedRetrieveError):
    pass
    # Message format: "Data file not found: /path/to/portugal_watersheds.parquet"


class DataUnavailableError(WatershedRetrieveError):
    pass


class R2ConnectionError(WatershedRetrieveError):
    pass
