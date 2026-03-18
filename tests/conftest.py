import os
from pathlib import Path

import pytest

import watershed_retrieve as wr

DEFAULT_DATA_DIR = Path("/Users/nicolaslazaro/Desktop/riv-extract-basins/output_parquet")
PORTUGAL_GAUGE_COUNT = 73
KNOWN_PORTUGAL_GAUGE = "04K-04A"  # also accessible as "04K/04A" (slash normalized)


@pytest.fixture(scope="session", autouse=True)
def configure_data_dir() -> None:
    data_dir = Path(os.environ.get("WATERSHED_RETRIEVE_DATA_DIR", str(DEFAULT_DATA_DIR)))
    wr.configure(data_dir)
