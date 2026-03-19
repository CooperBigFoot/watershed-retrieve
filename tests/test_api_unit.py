import geopandas as gpd
import pytest

import watershed_retrieve as wr
import watershed_retrieve._api as api_mod
from tests.conftest import FakeWatershedStore
from watershed_retrieve import (
    CountryNotFoundError,
    DataUnavailableError,
    GaugeNotFoundError,
)


class TestAvailableCountries:
    def test_returns_list(self) -> None:
        assert isinstance(wr.available_countries(), list)

    def test_has_18_entries(self) -> None:
        assert len(wr.available_countries()) == 18

    def test_is_sorted(self) -> None:
        countries = wr.available_countries()
        assert countries == sorted(countries)

    def test_contains_portugal(self) -> None:
        assert "portugal" in wr.available_countries()

    def test_all_lowercase(self) -> None:
        for c in wr.available_countries():
            assert c == c.lower()


class TestAvailableGauges:
    def test_returns_sorted_list(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        gauges = wr.available_gauges("portugal")
        assert gauges == sorted(gauges)

    def test_strips_prefix(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        gauges = wr.available_gauges("portugal")
        assert all(not g.startswith("portugal_") for g in gauges)

    def test_has_3_gauges(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        assert len(wr.available_gauges("portugal")) == 3

    def test_unavailable_region_raises(self) -> None:
        with pytest.raises(DataUnavailableError, match="not yet available"):
            wr.available_gauges("uk_ea")


class TestGetWatershed:
    def test_returns_single_row(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        gdf = wr.get_watershed("portugal", "G001")
        assert len(gdf) == 1

    def test_returns_geodataframe(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        gdf = wr.get_watershed("portugal", "G001")
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_invalid_gauge_raises(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        with pytest.raises(GaugeNotFoundError, match="ZZZZZ"):
            wr.get_watershed("portugal", "ZZZZZ")

    def test_invalid_country_raises(self) -> None:
        with pytest.raises(CountryNotFoundError):
            wr.get_watershed("narnia", "G001")

    def test_unavailable_region_raises(self) -> None:
        with pytest.raises(DataUnavailableError):
            wr.get_watershed("uk_nrfa", "G001")


class TestGetWatersheds:
    def test_all_gauges_returns_3(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        gdf = wr.get_watersheds("portugal")
        assert len(gdf) == 3

    def test_subset(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        gdf = wr.get_watersheds("portugal", ["G001"])
        assert len(gdf) == 1

    def test_missing_gauge_in_list_raises(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        with pytest.raises(GaugeNotFoundError, match="ZZZZZ"):
            wr.get_watersheds("portugal", ["G001", "ZZZZZ"])

    def test_returns_geodataframe(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        assert isinstance(wr.get_watersheds("portugal"), gpd.GeoDataFrame)

    def test_empty_gauge_ids_returns_empty(self, fake_store: FakeWatershedStore) -> None:
        api_mod._store = fake_store
        result = wr.get_watersheds("portugal", [])
        assert len(result) == 0
