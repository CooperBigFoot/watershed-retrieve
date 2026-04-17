from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely import from_wkb

from ._errors import (
    ConfigurationError,
    CorruptedDataError,
    DelineationError,
    InvalidArgumentError,
    WatershedRetrieveError,
)

try:
    import pyshed as _pyshed
except ImportError:
    _pyshed = None

_engine_cache: dict[str, Any] = {}


def _require_pyshed() -> None:
    """Raise if pyshed is not installed."""
    if _pyshed is None:
        raise ConfigurationError(
            "pyshed is not installed. pyshed currently ships only as an Apple "
            "Silicon macOS wheel. On macOS arm64, install with: "
            "pip install watershed-retrieve[delineate]. On other platforms, "
            "install pyshed from source (https://github.com/CooperBigFoot/shed) "
            "or contribute a wheel "
            "(https://github.com/CooperBigFoot/shed/blob/main/CONTRIBUTING.md)."
        )


def _get_engine(dataset: str | Path) -> Any:
    """Return a cached pyshed.Engine for the given dataset path."""
    _require_pyshed()
    key = str(Path(dataset).resolve())
    if key not in _engine_cache:
        try:
            _engine_cache[key] = _pyshed.Engine(key)
        except _pyshed.DatasetError as exc:
            raise WatershedRetrieveError(f"Failed to open HFX dataset: {exc}") from exc
    return _engine_cache[key]


def delineate(*, lat: float, lon: float, dataset: str | Path) -> gpd.GeoDataFrame:
    """Delineate the watershed upstream of a single outlet."""
    if not isinstance(dataset, (str, Path)):
        raise InvalidArgumentError(f"dataset must be a str or Path, got {type(dataset).__name__!r}")
    if not isinstance(lat, (int, float)):
        raise InvalidArgumentError(f"lat must be a number, got {type(lat).__name__!r}")
    if not isinstance(lon, (int, float)):
        raise InvalidArgumentError(f"lon must be a number, got {type(lon).__name__!r}")

    engine = _get_engine(dataset)

    try:
        result = engine.delineate(lat=lat, lon=lon)
    except ValueError as exc:
        raise InvalidArgumentError(str(exc)) from exc
    except _pyshed.ResolutionError as exc:
        raise DelineationError(f"Could not resolve outlet at lat={lat}, lon={lon}: {exc}") from exc
    except _pyshed.AssemblyError as exc:
        raise CorruptedDataError(f"Geometry assembly failed at lat={lat}, lon={lon}: {exc}") from exc
    except _pyshed.ShedError as exc:
        raise WatershedRetrieveError(str(exc)) from exc

    geometry = from_wkb(result.geometry_wkb)

    return gpd.GeoDataFrame(
        {"terminal_atom_id": [result.terminal_atom_id], "area_km2": [result.area_km2]},
        geometry=[geometry],
        crs="EPSG:4326",
    )
