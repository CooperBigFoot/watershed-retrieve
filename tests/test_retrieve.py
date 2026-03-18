import geopandas as gpd
import pytest

import watershed_retrieve as wr
from watershed_retrieve import CountryNotFoundError, GaugeNotFoundError, WatershedResult

KNOWN_GAUGE = "04K-04A"
KNOWN_GAUGE_SLASH = "04K/04A"
PORTUGAL_GAUGE_COUNT = 73


@pytest.mark.integration
class TestGetWatershed:
    def test_returns_geodataframe(self) -> None:
        result = wr.get_watershed("portugal", KNOWN_GAUGE)
        assert isinstance(result, gpd.GeoDataFrame)

    def test_has_one_row(self) -> None:
        result = wr.get_watershed("portugal", KNOWN_GAUGE)
        assert len(result) == 1

    def test_has_gauge_id_column(self) -> None:
        result = wr.get_watershed("portugal", KNOWN_GAUGE)
        assert "gauge_id" in result.columns

    def test_has_geometry_column(self) -> None:
        result = wr.get_watershed("portugal", KNOWN_GAUGE)
        assert "geometry" in result.columns

    def test_geometry_type(self) -> None:
        result = wr.get_watershed("portugal", KNOWN_GAUGE)
        geom_type = result.geometry.iloc[0].geom_type
        assert geom_type in ("Polygon", "MultiPolygon")

    def test_crs_is_4326(self) -> None:
        result = wr.get_watershed("portugal", KNOWN_GAUGE)
        assert result.crs.to_epsg() == 4326

    def test_slash_normalization(self) -> None:
        dash_result = wr.get_watershed("portugal", KNOWN_GAUGE)
        slash_result = wr.get_watershed("portugal", KNOWN_GAUGE_SLASH)
        assert dash_result["gauge_id"].iloc[0] == slash_result["gauge_id"].iloc[0]

    def test_invalid_country_raises(self) -> None:
        with pytest.raises(CountryNotFoundError):
            wr.get_watershed("narnia", KNOWN_GAUGE)

    def test_invalid_gauge_raises(self) -> None:
        with pytest.raises(GaugeNotFoundError):
            wr.get_watershed("portugal", "ZZZZZ-999")


@pytest.mark.integration
class TestGetWatershedWithRivers:
    def test_returns_watershed_result(self) -> None:
        result = wr.get_watershed_with_rivers("portugal", KNOWN_GAUGE)
        assert isinstance(result, WatershedResult)

    def test_watershed_has_one_row(self) -> None:
        result = wr.get_watershed_with_rivers("portugal", KNOWN_GAUGE)
        assert len(result.watershed) == 1

    def test_rivers_is_geodataframe_with_rows(self) -> None:
        result = wr.get_watershed_with_rivers("portugal", KNOWN_GAUGE)
        assert isinstance(result.rivers, gpd.GeoDataFrame)
        assert len(result.rivers) > 0

    def test_rivers_geometry_type(self) -> None:
        result = wr.get_watershed_with_rivers("portugal", KNOWN_GAUGE)
        geom_types = set(result.rivers.geometry.geom_type)
        assert geom_types <= {"LineString", "MultiLineString"}

    def test_can_unpack(self) -> None:
        result = wr.get_watershed_with_rivers("portugal", KNOWN_GAUGE)
        watershed, rivers = result
        assert isinstance(watershed, gpd.GeoDataFrame)
        assert isinstance(rivers, gpd.GeoDataFrame)


@pytest.mark.integration
class TestGetWatersheds:
    def test_no_gauge_ids_returns_all(self) -> None:
        result = wr.get_watersheds("portugal")
        assert len(result) == PORTUGAL_GAUGE_COUNT

    def test_with_gauge_ids_subset(self) -> None:
        subset = [KNOWN_GAUGE]
        result = wr.get_watersheds("portugal", gauge_ids=subset)
        assert len(result) == len(subset)

    def test_has_polygon_geometry(self) -> None:
        result = wr.get_watersheds("portugal")
        geom_types = set(result.geometry.geom_type)
        assert geom_types <= {"Polygon", "MultiPolygon"}

    def test_invalid_country_raises(self) -> None:
        with pytest.raises(CountryNotFoundError):
            wr.get_watersheds("narnia")

    def test_invalid_gauge_in_list_raises(self) -> None:
        with pytest.raises(GaugeNotFoundError):
            wr.get_watersheds("portugal", gauge_ids=[KNOWN_GAUGE, "ZZZZZ-999"])

    def test_returns_geodataframe(self) -> None:
        result = wr.get_watersheds("portugal")
        assert isinstance(result, gpd.GeoDataFrame)


@pytest.mark.integration
class TestGetWatershedsWithRivers:
    def test_returns_watershed_result(self) -> None:
        result = wr.get_watersheds_with_rivers("portugal")
        assert isinstance(result, WatershedResult)

    def test_watershed_has_expected_rows(self) -> None:
        result = wr.get_watersheds_with_rivers("portugal")
        assert len(result.watershed) == PORTUGAL_GAUGE_COUNT

    def test_rivers_has_rows(self) -> None:
        result = wr.get_watersheds_with_rivers("portugal")
        assert len(result.rivers) > 0
