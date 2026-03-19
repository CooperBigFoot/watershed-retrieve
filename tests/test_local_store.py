from pathlib import Path

import geopandas as gpd
import pytest

from watershed_retrieve._errors import DataNotFoundError
from watershed_retrieve._registry import CountryInfo
from watershed_retrieve._store import LocalParquetStore
from watershed_retrieve._types import CompositeGaugeId

PORTUGAL = CountryInfo(name="portugal", file_stem="portugal", gauge_prefix="portugal_")


class TestLocalParquetStoreReadWatersheds:
    def test_reads_all_rows(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_watersheds(PORTUGAL)
        assert len(gdf) == 3

    def test_returns_geodataframe(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_watersheds(PORTUGAL)
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_filters_by_gauge_ids(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_watersheds(PORTUGAL, [CompositeGaugeId("portugal_G001")])
        assert len(gdf) == 1
        assert gdf.iloc[0]["gauge_id"] == "portugal_G001"

    def test_crs_preserved(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_watersheds(PORTUGAL)
        assert gdf.crs.to_epsg() == 4326

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        store = LocalParquetStore(tmp_path)
        with pytest.raises(DataNotFoundError, match="Data file not found"):
            store.read_watersheds(PORTUGAL)


class TestLocalParquetStoreReadRivers:
    def test_reads_all_rows(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_rivers(PORTUGAL)
        assert len(gdf) == 3

    def test_returns_geodataframe(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_rivers(PORTUGAL)
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_filters_by_gauge_ids(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        gdf = store.read_rivers(PORTUGAL, [CompositeGaugeId("portugal_G001")])
        assert len(gdf) == 1


class TestLocalParquetStoreReadGaugeIds:
    def test_returns_all_gauge_ids(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        ids = store.read_gauge_ids(PORTUGAL)
        assert len(ids) == 3

    def test_returns_composite_gauge_ids(self, synthetic_parquet_dir: Path) -> None:
        store = LocalParquetStore(synthetic_parquet_dir)
        ids = store.read_gauge_ids(PORTUGAL)
        assert all(gid.startswith("portugal_") for gid in ids)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        store = LocalParquetStore(tmp_path)
        with pytest.raises(DataNotFoundError):
            store.read_gauge_ids(PORTUGAL)
