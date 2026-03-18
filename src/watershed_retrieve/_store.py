from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import geopandas as gpd
import pandas as pd

from ._errors import DataNotFoundError
from ._registry import CountryInfo
from ._types import CompositeGaugeId


@runtime_checkable
class WatershedStore(Protocol):
    def read_watersheds(
        self,
        country: CountryInfo,
        gauge_ids: list[CompositeGaugeId] | None = None,
    ) -> gpd.GeoDataFrame: ...

    def read_rivers(
        self,
        country: CountryInfo,
        gauge_ids: list[CompositeGaugeId] | None = None,
    ) -> gpd.GeoDataFrame: ...

    def read_gauge_ids(self, country: CountryInfo) -> list[CompositeGaugeId]: ...


class LocalParquetStore:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def _parquet_path(self, country: CountryInfo, suffix: str) -> Path:
        return self._base_dir / f"{country.file_stem}_{suffix}.parquet"

    def _ensure_exists(self, path: Path) -> None:
        if not path.exists():
            raise DataNotFoundError(f"Data file not found: {path}")

    def _read_geo(
        self,
        path: Path,
        gauge_ids: list[CompositeGaugeId] | None,
    ) -> gpd.GeoDataFrame:
        self._ensure_exists(path)
        filters: list[tuple[str, str, list[str]]] | None = [("gauge_id", "in", gauge_ids)] if gauge_ids else None
        return gpd.read_parquet(path, filters=filters)

    def read_watersheds(
        self,
        country: CountryInfo,
        gauge_ids: list[CompositeGaugeId] | None = None,
    ) -> gpd.GeoDataFrame:
        path = self._parquet_path(country, "watersheds")
        return self._read_geo(path, gauge_ids)

    def read_rivers(
        self,
        country: CountryInfo,
        gauge_ids: list[CompositeGaugeId] | None = None,
    ) -> gpd.GeoDataFrame:
        path = self._parquet_path(country, "rivers")
        return self._read_geo(path, gauge_ids)

    def read_gauge_ids(self, country: CountryInfo) -> list[CompositeGaugeId]:
        path = self._parquet_path(country, "watersheds")
        self._ensure_exists(path)
        df: pd.DataFrame = pd.read_parquet(path, columns=["gauge_id"])
        return [CompositeGaugeId(gid) for gid in df["gauge_id"]]
