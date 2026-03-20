from unittest.mock import patch

import pytest
from pyarrow.lib import ArrowInvalid

from watershed_retrieve import CorruptedDataError
from watershed_retrieve._errors import DataNotFoundError, R2ConnectionError
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


class TestR2ReadGaugeIdsErrors:
    def test_arrow_invalid_raises_corrupted_data_error(self) -> None:
        store = R2ParquetStore()
        with (
            patch("watershed_retrieve._store.pd.read_parquet", side_effect=ArrowInvalid("bad data")),
            pytest.raises(CorruptedDataError, match="corrupted"),
        ):
            store.read_gauge_ids(PORTUGAL)

    def test_file_not_found_raises_data_not_found_error(self) -> None:
        store = R2ParquetStore()
        with (
            patch("watershed_retrieve._store.pd.read_parquet", side_effect=FileNotFoundError("missing")),
            pytest.raises(DataNotFoundError, match="not found"),
        ):
            store.read_gauge_ids(PORTUGAL)

    def test_os_error_raises_r2_connection_error(self) -> None:
        store = R2ParquetStore()
        with (
            patch("watershed_retrieve._store.pd.read_parquet", side_effect=OSError("network fail")),
            pytest.raises(R2ConnectionError, match="Failed to fetch"),
        ):
            store.read_gauge_ids(PORTUGAL)


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
