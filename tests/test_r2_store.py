import pytest

from watershed_retrieve._registry import CountryInfo
from watershed_retrieve._store import _R2_BASE_URL, R2ParquetStore

PORTUGAL = CountryInfo(name="portugal", file_stem="portugal", gauge_prefix="portugal_")


class TestR2ParquetStoreUrlConstruction:
    def test_watersheds_url(self) -> None:
        store = R2ParquetStore()
        url = store._remote_path(PORTUGAL, "watersheds")
        assert url == f"{_R2_BASE_URL}/portugal_watersheds.parquet"

    def test_rivers_url(self) -> None:
        store = R2ParquetStore()
        url = store._remote_path(PORTUGAL, "rivers")
        assert url == f"{_R2_BASE_URL}/portugal_rivers.parquet"


@pytest.mark.network
class TestR2ParquetStoreLive:
    def test_read_gauge_ids_portugal(self) -> None:
        store = R2ParquetStore()
        ids = store.read_gauge_ids(PORTUGAL)
        assert len(ids) > 0
        assert all(gid.startswith("portugal_") for gid in ids)

    def test_read_watersheds_portugal_single(self) -> None:

        store = R2ParquetStore()
        ids = store.read_gauge_ids(PORTUGAL)
        gdf = store.read_watersheds(PORTUGAL, [ids[0]])
        assert len(gdf) == 1
        assert gdf.crs.to_epsg() == 4326
