from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd

from ._errors import DataUnavailableError, GaugeNotFoundError
from ._registry import CountryInfo, available_country_names, resolve_country
from ._store import LocalParquetStore, R2ParquetStore, WatershedStore
from ._types import Backend, CompositeGaugeId, GaugeId, WatershedResult

_store: WatershedStore | None = None


def _normalize_gauge_id(raw: str) -> GaugeId:
    return GaugeId(raw.strip().replace("/", "-"))


def _to_composite(country: CountryInfo, gauge_id: GaugeId) -> CompositeGaugeId:
    return CompositeGaugeId(f"{country.gauge_prefix}{gauge_id}")


def _strip_prefix(country: CountryInfo, composite_id: CompositeGaugeId) -> str:
    return composite_id.removeprefix(country.gauge_prefix)


def _check_data_available(info: CountryInfo) -> None:
    if not info.has_data:
        raise DataUnavailableError(
            f"Watershed data for '{info.name}' is not yet available. "
            "The MERIT-Hydro extraction engine was unable to produce basins for this region. "
            "The gauging stations exist in RivRetrieve but basin delineation is pending."
        )


def _default_backend() -> Backend:
    if os.environ.get("WATERSHED_RETRIEVE_DATA_DIR"):
        return Backend.LOCAL
    return Backend.R2


def _get_store() -> WatershedStore:
    global _store
    if _store is None:
        backend = _default_backend()
        if backend is Backend.LOCAL:
            _store = LocalParquetStore(Path(os.environ["WATERSHED_RETRIEVE_DATA_DIR"]))
        else:
            _store = R2ParquetStore()
    return _store


def configure(
    data_dir: str | Path | None = None, *, backend: Backend | None = None, cache_dir: Path | None = None
) -> None:
    global _store
    if data_dir is not None:
        _store = LocalParquetStore(Path(data_dir))
    elif backend is Backend.R2 or (backend is None and data_dir is None):
        _store = R2ParquetStore(cache_dir=cache_dir)
    elif backend is Backend.LOCAL:
        env_dir = os.environ.get("WATERSHED_RETRIEVE_DATA_DIR")
        if env_dir:
            _store = LocalParquetStore(Path(env_dir))
        else:
            raise ValueError("backend=Backend.LOCAL requires data_dir or WATERSHED_RETRIEVE_DATA_DIR env var")


def available_countries() -> list[str]:
    return available_country_names()


def available_gauges(country: str) -> list[str]:
    info = resolve_country(country)
    _check_data_available(info)
    store = _get_store()
    composites = store.read_gauge_ids(info)
    return sorted(_strip_prefix(info, cid) for cid in composites)


def get_watershed(country: str, gauge_id: str) -> gpd.GeoDataFrame:
    info = resolve_country(country)
    _check_data_available(info)
    gid = _normalize_gauge_id(gauge_id)
    composite = _to_composite(info, gid)
    store = _get_store()
    result = store.read_watersheds(info, [composite])
    if result.empty:
        raise GaugeNotFoundError(
            f"Gauge '{gauge_id}' not found in '{info.name}'. Use available_gauges('{info.name}') to list valid IDs."
        )
    return result


def get_watershed_with_rivers(country: str, gauge_id: str) -> WatershedResult:
    info = resolve_country(country)
    _check_data_available(info)
    gid = _normalize_gauge_id(gauge_id)
    composite = _to_composite(info, gid)
    store = _get_store()
    watershed = store.read_watersheds(info, [composite])
    if watershed.empty:
        raise GaugeNotFoundError(
            f"Gauge '{gauge_id}' not found in '{info.name}'. Use available_gauges('{info.name}') to list valid IDs."
        )
    rivers = store.read_rivers(info, [composite])
    return WatershedResult(watershed, rivers)


def get_watersheds(country: str, gauge_ids: list[str] | None = None) -> gpd.GeoDataFrame:
    info = resolve_country(country)
    _check_data_available(info)
    store = _get_store()
    if gauge_ids is not None:
        composites = [_to_composite(info, _normalize_gauge_id(g)) for g in gauge_ids]
        result = store.read_watersheds(info, composites)
        found = set(result["gauge_id"]) if not result.empty else set()
        for raw, composite in zip(gauge_ids, composites, strict=True):
            if composite not in found:
                raise GaugeNotFoundError(
                    f"Gauge '{raw}' not found in '{info.name}'. Use available_gauges('{info.name}') to list valid IDs."
                )
        return result
    return store.read_watersheds(info)


def get_watersheds_with_rivers(country: str, gauge_ids: list[str] | None = None) -> WatershedResult:
    info = resolve_country(country)
    _check_data_available(info)
    store = _get_store()
    if gauge_ids is not None:
        composites = [_to_composite(info, _normalize_gauge_id(g)) for g in gauge_ids]
        watershed = store.read_watersheds(info, composites)
        found = set(watershed["gauge_id"]) if not watershed.empty else set()
        for raw, composite in zip(gauge_ids, composites, strict=True):
            if composite not in found:
                raise GaugeNotFoundError(
                    f"Gauge '{raw}' not found in '{info.name}'. Use available_gauges('{info.name}') to list valid IDs."
                )
        rivers = store.read_rivers(info, composites)
        return WatershedResult(watershed, rivers)
    watershed = store.read_watersheds(info)
    rivers = store.read_rivers(info)
    return WatershedResult(watershed, rivers)
