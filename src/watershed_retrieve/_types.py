from enum import Enum, auto
from typing import NamedTuple, NewType

import geopandas as gpd

GaugeId = NewType("GaugeId", str)  # original ID after normalization: "04K-04A"
CompositeGaugeId = NewType("CompositeGaugeId", str)  # parquet key: "portugal_04K-04A"


class Backend(Enum):
    R2 = auto()
    LOCAL = auto()


class WatershedResult(NamedTuple):
    watershed: gpd.GeoDataFrame
    rivers: gpd.GeoDataFrame
