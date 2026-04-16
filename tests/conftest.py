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
    import watershed_retrieve._delineate as delin_mod
    from watershed_retrieve._types import Fabric

    api_mod._store = None
    api_mod._fabric = Fabric.MERIT
    delin_mod._engine_cache.clear()
    yield
    api_mod._store = None
    api_mod._fabric = Fabric.MERIT
    delin_mod._engine_cache.clear()


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
# WKB helper for delineation tests
# ---------------------------------------------------------------------------


def make_wkb_polygon(minx: float, miny: float, maxx: float, maxy: float) -> bytes:
    """Create a minimal WKB Polygon (LE, type=3, 1 ring, 5 points)."""
    import struct

    coords = [
        (minx, miny),
        (maxx, miny),
        (maxx, maxy),
        (minx, maxy),
        (minx, miny),
    ]
    buf = struct.pack("<bII", 1, 3, 1)  # LE, Polygon, 1 ring
    buf += struct.pack("<I", 5)  # 5 points
    for x, y in coords:
        buf += struct.pack("<dd", x, y)
    return buf


# ---------------------------------------------------------------------------
# FakePyshed — fake pyshed module for delineation unit tests
# ---------------------------------------------------------------------------


class _FakeShedError(Exception):
    pass


class _FakeDatasetError(_FakeShedError):
    pass


class _FakeResolutionError(_FakeShedError):
    pass


class _FakeAssemblyError(_FakeShedError):
    pass


class FakeDelineationResult:
    def __init__(self, *, terminal_atom_id: int, area_km2: float, geometry_wkb: bytes) -> None:
        self.terminal_atom_id = terminal_atom_id
        self.area_km2 = area_km2
        self.geometry_wkb = geometry_wkb


class FakePyshedEngine:
    """Fake pyshed.Engine for unit tests.

    Behaviors: "success" returns a valid result, "resolution_error" raises ResolutionError,
    "dataset_error" raises DatasetError, "assembly_error" raises AssemblyError,
    "shed_error" raises ShedError.
    """

    def __init__(self, dataset_path: str, behavior: str = "success") -> None:
        self._behavior = behavior

    def delineate(self, *, lat: float, lon: float) -> FakeDelineationResult:
        if self._behavior == "resolution_error":
            raise _FakeResolutionError("outlet outside all catchments")
        if self._behavior == "dataset_error":
            raise _FakeDatasetError("bad dataset")
        if self._behavior == "assembly_error":
            raise _FakeAssemblyError("geometry assembly failed")
        if self._behavior == "shed_error":
            raise _FakeShedError("unexpected engine error")
        if self._behavior == "value_error":
            raise ValueError(f"latitude {lat} is outside [-90, 90]")
        return FakeDelineationResult(
            terminal_atom_id=42,
            area_km2=123.45,
            geometry_wkb=make_wkb_polygon(lon - 0.1, lat - 0.1, lon + 0.1, lat + 0.1),
        )


class FakePyshedModule:
    """Namespace object mimicking the pyshed module for injection into _delineate."""

    ShedError = _FakeShedError
    DatasetError = _FakeDatasetError
    ResolutionError = _FakeResolutionError
    AssemblyError = _FakeAssemblyError
    Engine = FakePyshedEngine


@pytest.fixture
def fake_pyshed() -> FakePyshedModule:
    """Return a FakePyshedModule for injection into _delineate."""
    return FakePyshedModule()


@pytest.fixture
def patch_pyshed(fake_pyshed: FakePyshedModule):
    """Inject FakePyshedModule into _delineate so delineate() uses fakes."""
    import watershed_retrieve._delineate as delin_mod

    original = delin_mod._pyshed
    delin_mod._pyshed = fake_pyshed
    yield fake_pyshed
    delin_mod._pyshed = original


# ---------------------------------------------------------------------------
# Synthetic HFX dataset fixture (for integration tests requiring real pyshed)
# ---------------------------------------------------------------------------


@pytest.fixture
def hfx_dataset(tmp_path: Path) -> str:
    """Create a synthetic 3-atom HFX dataset and return its path as a string.

    Requires pyarrow. Skips the test if pyshed is not importable.
    """
    pytest.importorskip("pyshed")

    import json

    import pyarrow as pa
    import pyarrow.ipc
    import pyarrow.parquet

    # Atom specs: linear chain (1→2→3)
    atoms = [
        {"id": 1, "minx": 0.5, "miny": 0.0, "maxx": 0.9, "maxy": 0.4},
        {"id": 2, "minx": 1.0, "miny": 0.0, "maxx": 1.4, "maxy": 0.4},
        {"id": 3, "minx": 1.5, "miny": 0.0, "maxx": 1.9, "maxy": 0.4},
    ]

    # manifest.json
    manifest = {
        "format_version": "0.1",
        "fabric_name": "testfabric",
        "crs": "EPSG:4326",
        "topology": "tree",
        "terminal_sink_id": 0,
        "bbox": [-180.0, -90.0, 180.0, 90.0],
        "atom_count": 3,
        "created_at": "2026-01-01T00:00:00Z",
        "adapter_version": "test-v1",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))

    # graph.arrow — linear chain: atom 1 has no upstream, 2 has [1], 3 has [2]
    graph_schema = pa.schema(
        [
            pa.field("id", pa.int64(), nullable=False),
            pa.field("upstream_ids", pa.list_(pa.field("item", pa.int64(), nullable=True)), nullable=False),
        ]
    )
    ids = pa.array([1, 2, 3], type=pa.int64())
    upstream_ids = pa.array(
        [[], [1], [2]],
        type=pa.list_(pa.field("item", pa.int64(), nullable=True)),
    )
    batch = pa.record_batch([ids, upstream_ids], schema=graph_schema)
    with open(tmp_path / "graph.arrow", "wb") as fh, pa.ipc.new_file(fh, graph_schema) as writer:
        writer.write_batch(batch)

    # catchments.parquet
    catchment_schema = pa.schema(
        [
            pa.field("id", pa.int64(), nullable=False),
            pa.field("area_km2", pa.float32(), nullable=False),
            pa.field("up_area_km2", pa.float32(), nullable=True),
            pa.field("bbox_minx", pa.float32(), nullable=False),
            pa.field("bbox_miny", pa.float32(), nullable=False),
            pa.field("bbox_maxx", pa.float32(), nullable=False),
            pa.field("bbox_maxy", pa.float32(), nullable=False),
            pa.field("geometry", pa.binary(), nullable=False),
        ]
    )
    table = pa.table(
        {
            "id": pa.array([a["id"] for a in atoms], type=pa.int64()),
            "area_km2": pa.array([10.0] * 3, type=pa.float32()),
            "up_area_km2": pa.array([None] * 3, type=pa.float32()),
            "bbox_minx": pa.array([a["minx"] for a in atoms], type=pa.float32()),
            "bbox_miny": pa.array([a["miny"] for a in atoms], type=pa.float32()),
            "bbox_maxx": pa.array([a["maxx"] for a in atoms], type=pa.float32()),
            "bbox_maxy": pa.array([a["maxy"] for a in atoms], type=pa.float32()),
            "geometry": pa.array(
                [make_wkb_polygon(a["minx"], a["miny"], a["maxx"], a["maxy"]) for a in atoms],
                type=pa.binary(),
            ),
        },
        schema=catchment_schema,
    )
    with open(tmp_path / "catchments.parquet", "wb") as fh, pa.parquet.ParquetWriter(fh, catchment_schema) as writer:
        writer.write_table(table)

    return str(tmp_path)


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
