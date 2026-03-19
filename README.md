# watershed-retrieve

[![PyPI version](https://img.shields.io/pypi/v/watershed-retrieve)](https://pypi.org/project/watershed-retrieve/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)

Instant access to ~60,000 pre-delineated MERIT-Hydro watershed boundaries and river networks across 16 countries, served as GeoParquet. No data download required — basins are fetched on demand from a public CDN and cached locally.

## Background

This library is a community contribution to the [RivRetrieve](https://github.com/kratzert/RivRetrieve-Python) ecosystem. Where RivRetrieve provides observed streamflow time series for gauging stations worldwide, **watershed-retrieve** adds the corresponding watershed boundaries and river networks, delineated on the [MERIT-Hydro](http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/) digital elevation model.

See the original proposal: [kratzert/RivRetrieve-Python#87](https://github.com/kratzert/RivRetrieve-Python/issues/87).

## Installation

```bash
pip install watershed-retrieve
```

## Quick Start

```python
import watershed_retrieve as wr

# Zero-config — data is fetched from R2 CDN and cached locally
watershed = wr.get_watershed("portugal", "04K/04A")

# With river network
watershed, rivers = wr.get_watershed_with_rivers("portugal", "04K/04A")

# Bulk retrieval — all watersheds for a country
all_watersheds = wr.get_watersheds("portugal")
```

To use a local data directory instead of the CDN:

```python
# Option 1: Environment variable
# export WATERSHED_RETRIEVE_DATA_DIR=/path/to/parquet/files

# Option 2: Programmatic
wr.configure("/path/to/parquet/files")

# Option 3: Explicit backend selection
from watershed_retrieve import Backend
wr.configure(backend=Backend.R2, cache_dir=Path("~/.my-cache"))
```

## API Reference

### Discovery

```python
# List all supported countries
wr.available_countries()
# -> ['australia', 'brazil', 'canada', ..., 'usa']

# List gauge IDs for a country
wr.available_gauges("portugal")
# -> ['02G-02H', '02O-01H', ..., '16J-01H']  (73 gauges)
```

### Single Watershed

```python
# Watershed boundary (GeoDataFrame, 1 row)
gdf = wr.get_watershed("portugal", "04K/04A")

# Watershed + river network (WatershedResult — unpackable NamedTuple)
result = wr.get_watershed_with_rivers("portugal", "04K/04A")
watershed, rivers = result
```

### Bulk Retrieval

```python
# All watersheds for a country
gdf = wr.get_watersheds("portugal")  # -> GeoDataFrame (73 rows)

# Subset by gauge IDs
gdf = wr.get_watersheds("portugal", ["04K/04A", "05G/01A"])

# With rivers
result = wr.get_watersheds_with_rivers("portugal")
result.watershed  # GeoDataFrame
result.rivers     # GeoDataFrame
```

### Gauge ID Normalization

Slashes are automatically normalized to dashes:

```python
wr.get_watershed("portugal", "04K/04A")   # slash
wr.get_watershed("portugal", "04K-04A")   # dash — equivalent
```

### Errors

```python
from watershed_retrieve import (
    WatershedRetrieveError,     # base class
    CountryNotFoundError,       # invalid country name
    GaugeNotFoundError,         # gauge ID not in dataset
    DataNotFoundError,          # parquet file missing
    DataUnavailableError,       # region exists but data not yet extracted
    R2ConnectionError,          # CDN fetch failed
)
```

`DataUnavailableError` is raised for regions where gauging stations are registered in RivRetrieve but MERIT-Hydro basin delineation is pending (e.g., UK regions — the British Isles fall outside MERIT-Hydro coverage).

## Supported Countries

| Country | Gauges | Status |
|---------|--------|--------|
| Australia | ~5,200 | Available |
| Brazil | ~4,300 | Available |
| Canada | ~5,800 | Available |
| Chile | ~500 | Available |
| Czech Republic | ~400 | Available |
| France | ~5,400 | Available |
| Germany | ~500 | Available |
| Japan | ~1,200 | Available |
| Lithuania | ~70 | Available |
| Norway | ~600 | Available |
| Poland | ~600 | Available |
| Portugal | 73 | Available |
| Slovenia | ~200 | Available |
| South Africa | ~900 | Available |
| Spain | ~600 | Available |
| UK (EA) | ~1,500 | Pending — MERIT-Hydro coverage gap |
| UK (NRFA) | ~1,500 | Pending — MERIT-Hydro coverage gap |
| USA | ~32,000 | Available |

## Development

```bash
# Install
git clone https://github.com/CooperBigFoot/watershed-retrieve.git
cd watershed-retrieve
uv sync

# Unit tests (no data or network needed)
uv run pytest tests/ -v -m "not integration and not network"

# Integration tests (requires local parquet data)
WATERSHED_RETRIEVE_DATA_DIR=/path/to/data uv run pytest tests/ -v -m integration

# Lint & format
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guidelines.

## License

[MIT](LICENSE)
