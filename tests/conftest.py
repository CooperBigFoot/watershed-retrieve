from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import LineString, box

import watershed_retrieve as wr
from watershed_retrieve._api import _store as _sentinel  # noqa: F401 — only for type reference
from watershed_retrieve._registry import CountryInfo
from watershed_retrieve._types import CompositeGaugeId

PORTUGAL_GAUGE_COUNT = 73
KNOWN_PORTUGAL_GAUGE = "04K-04A"


# ---------------------------------------------------------------------------
# Marker-based skip hooks
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--run-network", action="store_true", default=False, help="Run tests that hit the R2 CDN")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    has_data_dir = bool(os.environ.get("WATERSHED_RETRIEVE_DATA_DIR"))
    run_network = config.getoption("--run-network", default=False) or bool(
        os.environ.get("WATERSHED_RETRIEVE_RUN_NETWORK")
    )

    skip_integration = pytest.mark.skip(reason="needs WATERSHED_RETRIEVE_DATA_DIR")
    skip_network = pytest.mark.skip(reason="needs --run-network or WATERSHED_RETRIEVE_RUN_NETWORK=1")

    for item in items:
        if "integration" in item.keywords and not has_data_dir:
            item.add_marker(skip_integration)
        if "network" in item.keywords and not run_network:
            item.add_marker(skip_network)


# ---------------------------------------------------------------------------
# Global store reset (autouse) — isolates every test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_global_store() -> None:
    import watershed_retrieve._api as api_mod

    api_mod._store = None
    yield
    api_mod._store = None


# ---------------------------------------------------------------------------
# Integration fixture — configures real data dir when env var is set
# ---------------------------------------------------------------------------


@pytest.fixture
def configure_data_dir() -> None:
    data_dir = os.environ.get("WATERSHED_RETRIEVE_DATA_DIR")
    if data_dir:
        wr.configure(data_dir)


# ---------------------------------------------------------------------------
# FakeWatershedStore — satisfies WatershedStore Protocol for unit tests
# ---------------------------------------------------------------------------


class FakeWatershedStore:
    def __init__(self, watersheds: dict[str, gpd.GeoDataFrame], rivers: dict[str, gpd.GeoDataFrame]) -> None:
        self._watersheds = watersheds
        self._rivers = rivers

    def read_watersheds(
        self,
        country: CountryInfo,
        gauge_ids: list[CompositeGaugeId] | None = None,
    ) -> gpd.GeoDataFrame:
        gdf = self._watersheds.get(country.file_stem, gpd.GeoDataFrame())
        if gauge_ids is not None and not gdf.empty:
            gdf = gdf[gdf["gauge_id"].isin(gauge_ids)]
        return gdf

    def read_rivers(
        self,
        country: CountryInfo,
        gauge_ids: list[CompositeGaugeId] | None = None,
    ) -> gpd.GeoDataFrame:
        gdf = self._rivers.get(country.file_stem, gpd.GeoDataFrame())
        if gauge_ids is not None and not gdf.empty:
            gdf = gdf[gdf["gauge_id"].isin(gauge_ids)]
        return gdf

    def read_gauge_ids(self, country: CountryInfo) -> list[CompositeGaugeId]:
        gdf = self._watersheds.get(country.file_stem, gpd.GeoDataFrame())
        if gdf.empty:
            return []
        return [CompositeGaugeId(gid) for gid in gdf["gauge_id"]]


# ---------------------------------------------------------------------------
# Synthetic parquet directory fixture
# ---------------------------------------------------------------------------


def _make_synthetic_geodataframe(
    gauge_ids: list[str],
    geom_factory: callable,
    crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"gauge_id": gauge_ids},
        geometry=[geom_factory(i) for i in range(len(gauge_ids))],
        crs=crs,
    )


@pytest.fixture
def synthetic_parquet_dir(tmp_path: Path) -> Path:
    gauge_ids = ["portugal_G001", "portugal_G002", "portugal_G003"]

    watersheds = _make_synthetic_geodataframe(
        gauge_ids,
        geom_factory=lambda i: box(i, i, i + 1, i + 1),
    )
    rivers = _make_synthetic_geodataframe(
        gauge_ids,
        geom_factory=lambda i: LineString([(i, i), (i + 1, i + 1)]),
    )

    watersheds.to_parquet(tmp_path / "portugal_watersheds.parquet")
    rivers.to_parquet(tmp_path / "portugal_rivers.parquet")
    return tmp_path


# ---------------------------------------------------------------------------
# FakeStore fixture — pre-built with 3 synthetic Portugal gauges
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_store(synthetic_parquet_dir: Path) -> FakeWatershedStore:
    gauge_ids = ["portugal_G001", "portugal_G002", "portugal_G003"]

    watersheds_gdf = _make_synthetic_geodataframe(
        gauge_ids,
        geom_factory=lambda i: box(i, i, i + 1, i + 1),
    )
    rivers_gdf = _make_synthetic_geodataframe(
        gauge_ids,
        geom_factory=lambda i: LineString([(i, i), (i + 1, i + 1)]),
    )

    return FakeWatershedStore(
        watersheds={"portugal": watersheds_gdf},
        rivers={"portugal": rivers_gdf},
    )
