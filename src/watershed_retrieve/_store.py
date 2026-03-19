from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

import geopandas as gpd
import pandas as pd
from pyarrow.fs import FSSpecHandler, PyFileSystem

from ._errors import DataNotFoundError, R2ConnectionError
from ._registry import CountryInfo
from ._types import CompositeGaugeId

_R2_BASE_URL = "https://pub-52975bdd539f43819da3692334f4999c.r2.dev/watershed-retrieve/v1"
_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "watershed-retrieve"

log = logging.getLogger(__name__)


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


class R2ParquetStore:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir or _DEFAULT_CACHE_DIR
        self._fs = self._build_fs()

    def _build_fs(self) -> PyFileSystem:
        import fsspec

        http_fs = fsspec.filesystem("simplecache", target_protocol="https", cache_storage=str(self._cache_dir))
        return PyFileSystem(FSSpecHandler(http_fs))

    def _remote_path(self, country: CountryInfo, suffix: str) -> str:
        return f"{_R2_BASE_URL}/{country.file_stem}_{suffix}.parquet"

    def _read_geo(self, url: str, gauge_ids: list[CompositeGaugeId] | None) -> gpd.GeoDataFrame:
        filters: list[tuple[str, str, list[str]]] | None = [("gauge_id", "in", gauge_ids)] if gauge_ids else None
        try:
            return gpd.read_parquet(url, filesystem=self._fs, filters=filters)
        except FileNotFoundError:
            raise DataNotFoundError(f"Remote data file not found: {url}") from None
        except (OSError, ConnectionError) as exc:
            raise R2ConnectionError(f"Failed to fetch data from R2: {exc}") from exc

    def read_watersheds(
        self, country: CountryInfo, gauge_ids: list[CompositeGaugeId] | None = None
    ) -> gpd.GeoDataFrame:
        url = self._remote_path(country, "watersheds")
        return self._read_geo(url, gauge_ids)

    def read_rivers(self, country: CountryInfo, gauge_ids: list[CompositeGaugeId] | None = None) -> gpd.GeoDataFrame:
        url = self._remote_path(country, "rivers")
        return self._read_geo(url, gauge_ids)

    def read_gauge_ids(self, country: CountryInfo) -> list[CompositeGaugeId]:
        url = self._remote_path(country, "watersheds")
        try:
            df: pd.DataFrame = pd.read_parquet(url, columns=["gauge_id"], filesystem=self._fs)
        except FileNotFoundError:
            raise DataNotFoundError(f"Remote data file not found: {url}") from None
        except (OSError, ConnectionError) as exc:
            raise R2ConnectionError(f"Failed to fetch data from R2: {exc}") from exc
        return [CompositeGaugeId(gid) for gid in df["gauge_id"]]
