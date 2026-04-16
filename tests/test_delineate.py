from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest

import watershed_retrieve as wr
from tests.conftest import FakePyshedEngine
from watershed_retrieve._errors import (
    ConfigurationError,
    DelineationError,
    InvalidArgumentError,
    WatershedRetrieveError,
)


class TestDelineate:
    """Happy path tests for delineate()."""

    def test_returns_geodataframe(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert isinstance(result, gpd.GeoDataFrame)

    def test_single_row(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert len(result) == 1

    def test_has_terminal_atom_id_column(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert "terminal_atom_id" in result.columns

    def test_has_area_km2_column(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert "area_km2" in result.columns

    def test_has_geometry_column(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert "geometry" in result.columns

    def test_crs_is_4326(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert result.crs.to_epsg() == 4326

    def test_geometry_type(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert result.geometry.iloc[0].geom_type in ("Polygon", "MultiPolygon")

    def test_area_is_positive(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert result["area_km2"].iloc[0] > 0

    def test_terminal_atom_id_value(self, patch_pyshed, tmp_path):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        assert result["terminal_atom_id"].iloc[0] == 42  # from FakePyshedEngine


class TestDelineateErrorMapping:
    """Exception mapping from pyshed → watershed-retrieve errors."""

    def test_resolution_error_maps_to_delineation_error(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="resolution_error")

        with pytest.raises(DelineationError, match="Could not resolve outlet"):
            wr.delineate(lat=0.2, lon=1.7, dataset=dataset)

    def test_assembly_error_maps_to_delineation_error(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="assembly_error")

        with pytest.raises(DelineationError, match="Geometry assembly failed"):
            wr.delineate(lat=0.2, lon=1.7, dataset=dataset)

    def test_shed_error_maps_to_watershed_retrieve_error(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="shed_error")

        with pytest.raises(WatershedRetrieveError):
            wr.delineate(lat=0.2, lon=1.7, dataset=dataset)

    def test_value_error_maps_to_invalid_argument_error(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="value_error")

        with pytest.raises(InvalidArgumentError, match="latitude"):
            wr.delineate(lat=91.0, lon=0.0, dataset=dataset)

    def test_error_includes_coordinates(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="resolution_error")

        with pytest.raises(DelineationError, match="lat=0.2") as exc_info:
            wr.delineate(lat=0.2, lon=1.7, dataset=dataset)
        assert "lon=1.7" in str(exc_info.value)

    def test_exceptions_are_chained(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="resolution_error")

        with pytest.raises(DelineationError) as exc_info:
            wr.delineate(lat=0.2, lon=1.7, dataset=dataset)
        assert exc_info.value.__cause__ is not None

    def test_dataset_error_during_engine_init_maps_to_watershed_retrieve_error(self, patch_pyshed, tmp_path):
        """DatasetError raised by Engine() constructor maps to WatershedRetrieveError."""
        # Patch Engine to raise DatasetError on construction
        original_engine = patch_pyshed.Engine

        class RaisingEngine:
            def __init__(self, path: str) -> None:
                raise patch_pyshed.DatasetError("bad dataset")

        patch_pyshed.Engine = RaisingEngine
        try:
            with pytest.raises(WatershedRetrieveError, match="Failed to open HFX dataset"):
                wr.delineate(lat=0.2, lon=1.7, dataset=str(tmp_path))
        finally:
            patch_pyshed.Engine = original_engine


class TestDelineateNoPyshed:
    """Tests for when pyshed is not installed."""

    def test_raises_configuration_error(self):
        import watershed_retrieve._delineate as delin_mod

        original = delin_mod._pyshed
        delin_mod._pyshed = None
        try:
            with pytest.raises(ConfigurationError, match="pyshed is not installed"):
                wr.delineate(lat=0.0, lon=0.0, dataset="/fake")
        finally:
            delin_mod._pyshed = original

    def test_error_message_includes_install_instructions(self):
        import watershed_retrieve._delineate as delin_mod

        original = delin_mod._pyshed
        delin_mod._pyshed = None
        try:
            with pytest.raises(ConfigurationError, match="pip install watershed-retrieve"):
                wr.delineate(lat=0.0, lon=0.0, dataset="/fake")
        finally:
            delin_mod._pyshed = original


class TestDelineateInputValidation:
    """Type validation for lat/lon parameters."""

    def test_non_numeric_lat_raises_invalid_argument_error(self, patch_pyshed):
        with pytest.raises(InvalidArgumentError, match="lat must be a number"):
            wr.delineate(lat="hello", lon=1.0, dataset="/fake")  # type: ignore[arg-type]

    def test_non_numeric_lon_raises_invalid_argument_error(self, patch_pyshed):
        with pytest.raises(InvalidArgumentError, match="lon must be a number"):
            wr.delineate(lat=1.0, lon=None, dataset="/fake")  # type: ignore[arg-type]


class TestDelineateEngineCache:
    """Engine caching behavior."""

    def test_same_dataset_reuses_engine(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        wr.delineate(lat=0.2, lon=1.7, dataset=dataset)
        wr.delineate(lat=0.2, lon=1.7, dataset=dataset)

        key = str(Path(dataset).resolve())
        assert key in delin_mod._engine_cache

    def test_different_datasets_create_separate_engines(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset_a = str(tmp_path / "a")
        dataset_b = str(tmp_path / "b")
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()

        wr.delineate(lat=0.2, lon=1.7, dataset=dataset_a)
        wr.delineate(lat=0.2, lon=1.7, dataset=dataset_b)

        assert len(delin_mod._engine_cache) == 2

    def test_cache_is_keyed_on_resolved_path(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        wr.delineate(lat=0.2, lon=1.7, dataset=dataset)

        key = str(Path(dataset).resolve())
        assert key in delin_mod._engine_cache
        # The raw (possibly non-resolved) string should not be stored separately
        assert len(delin_mod._engine_cache) == 1


class TestDelineationErrorHierarchy:
    """Error hierarchy relationships."""

    def test_delineation_error_is_watershed_retrieve_error(self):
        assert issubclass(DelineationError, WatershedRetrieveError)

    def test_invalid_argument_error_is_watershed_retrieve_error(self):
        assert issubclass(InvalidArgumentError, WatershedRetrieveError)

    def test_configuration_error_is_watershed_retrieve_error(self):
        assert issubclass(ConfigurationError, WatershedRetrieveError)

    def test_catching_root_catches_delineation(self, patch_pyshed, tmp_path):
        import watershed_retrieve._delineate as delin_mod

        dataset = str(tmp_path)
        key = str(Path(dataset).resolve())
        delin_mod._engine_cache[key] = FakePyshedEngine(key, behavior="resolution_error")

        with pytest.raises(WatershedRetrieveError):
            wr.delineate(lat=0.2, lon=1.7, dataset=dataset)


class TestDelineateIntegration:
    """Integration tests that require real pyshed and a synthetic HFX dataset."""

    def test_returns_geodataframe(self, hfx_dataset):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=hfx_dataset)
        assert isinstance(result, gpd.GeoDataFrame)

    def test_correct_schema(self, hfx_dataset):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=hfx_dataset)
        assert "terminal_atom_id" in result.columns
        assert "area_km2" in result.columns
        assert "geometry" in result.columns

    def test_correct_crs(self, hfx_dataset):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=hfx_dataset)
        assert result.crs.to_epsg() == 4326

    def test_geometry_is_valid(self, hfx_dataset):
        result = wr.delineate(lat=0.2, lon=1.7, dataset=hfx_dataset)
        geom = result.geometry.iloc[0]
        assert not geom.is_empty
        assert geom.is_valid

    def test_outside_dataset_raises_delineation_error(self, hfx_dataset):
        with pytest.raises(DelineationError, match="Could not resolve"):
            wr.delineate(lat=50.0, lon=50.0, dataset=hfx_dataset)
