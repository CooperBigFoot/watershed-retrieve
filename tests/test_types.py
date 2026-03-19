import geopandas as gpd
from shapely.geometry import box

from watershed_retrieve._types import Backend, WatershedResult


class TestWatershedResult:
    def test_is_named_tuple(self) -> None:
        gdf = gpd.GeoDataFrame({"gauge_id": ["g1"]}, geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
        result = WatershedResult(watershed=gdf, rivers=gdf)
        assert hasattr(result, "_fields")

    def test_fields(self) -> None:
        gdf = gpd.GeoDataFrame({"gauge_id": ["g1"]}, geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
        result = WatershedResult(watershed=gdf, rivers=gdf)
        assert result._fields == ("watershed", "rivers")

    def test_unpackable(self) -> None:
        gdf1 = gpd.GeoDataFrame({"gauge_id": ["g1"]}, geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
        gdf2 = gpd.GeoDataFrame({"gauge_id": ["g2"]}, geometry=[box(1, 1, 2, 2)], crs="EPSG:4326")
        w, r = WatershedResult(gdf1, gdf2)
        assert len(w) == 1
        assert len(r) == 1

    def test_field_access(self) -> None:
        gdf = gpd.GeoDataFrame({"gauge_id": ["g1"]}, geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
        result = WatershedResult(watershed=gdf, rivers=gdf)
        assert isinstance(result.watershed, gpd.GeoDataFrame)
        assert isinstance(result.rivers, gpd.GeoDataFrame)


class TestBackend:
    def test_r2_variant(self) -> None:
        assert Backend.R2.name == "R2"

    def test_local_variant(self) -> None:
        assert Backend.LOCAL.name == "LOCAL"

    def test_two_variants(self) -> None:
        assert len(Backend) == 2
