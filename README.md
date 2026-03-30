# watershed-retrieve

[![PyPI version](https://img.shields.io/pypi/v/watershed-retrieve)](https://pypi.org/project/watershed-retrieve/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)

Instant access to ~60,000 pre-delineated watershed boundaries and river networks across 16 countries, served as GeoParquet. Supports multiple hydrofabrics (MERIT-Hydro and HydroSHEDS v1). No data download required — basins are fetched on demand from a public CDN and cached locally.

## Background

This library is a community contribution to the [RivRetrieve](https://github.com/kratzert/RivRetrieve-Python) ecosystem. Where RivRetrieve provides observed streamflow time series for gauging stations worldwide, **watershed-retrieve** adds the corresponding watershed boundaries and river networks.

Delineation is available on two hydrofabrics:
- **[MERIT-Hydro](http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/)** — ~90m global hydrography (default)
- **[HydroSHEDS v1](https://www.hydrosheds.org/)** — ~90m global hydrography, alternative dataset

The watershed delineation was performed using a Rust reimplementation of the algorithm described in [mheberger/delineator](https://github.com/mheberger/delineator). This is the same methodology used by [CAMELS-DE](https://doi.org/10.5194/essd-16-5625-2024) (Loritz et al., 2024) to derive consistent catchment boundaries for 1582 gauging stations across Germany from MERIT Hydro.

See the original proposal: [kratzert/RivRetrieve-Python#87](https://github.com/kratzert/RivRetrieve-Python/issues/87).

## Installation

```bash
pip install watershed-retrieve
```

## Quick Start

```python
import watershed_retrieve as wr

# Zero-config — data is fetched from R2 CDN and cached locally (MERIT-Hydro by default)
watershed = wr.get_watershed("portugal", "04K/04A")

# With river network
watershed, rivers = wr.get_watershed_with_rivers("portugal", "04K/04A")

# Bulk retrieval — all watersheds for a country
all_watersheds = wr.get_watersheds("portugal")
```

### Selecting a hydrofabric

```python
from watershed_retrieve import Fabric

# Use HydroSHEDS v1 instead of MERIT-Hydro
wr.configure(fabric=Fabric.HYDROSHEDS_V1)

# All subsequent calls use HydroSHEDS data
watershed = wr.get_watershed("portugal", "04K/04A")

# Switch back to MERIT-Hydro
wr.configure(fabric=Fabric.MERIT)
```

### Local data directory

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
# -> ['02G-02H', '02O-01H', ..., '16J-01H']  (~710 gauges)
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
gdf = wr.get_watersheds("portugal")  # -> GeoDataFrame (~710 rows)

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

`DataUnavailableError` is raised for regions where gauging stations are registered in RivRetrieve but basin delineation is pending (e.g., UK regions — the British Isles fall outside MERIT-Hydro coverage).

## Supported Countries

| Country | MERIT-Hydro | HydroSHEDS v1 | Status |
|---------|-------------|---------------|--------|
| Australia | ~6,210 | ~6,240 | Available |
| Brazil | ~4,600 | ~4,610 | Available |
| Canada | ~7,630 | ~7,240 | Available |
| Chile | ~540 | ~530 | Available |
| Czech Republic | ~820 | ~820 | Available |
| France | ~5,330 | ~5,360 | Available |
| Germany | ~190 | ~190 | Available |
| Japan | ~820 | ~810 | Available |
| Lithuania | ~100 | ~100 | Available |
| Norway | ~4,540 | ~1,460 | Available |
| Poland | ~1,300 | ~1,300 | Available |
| Portugal | ~710 | ~710 | Available |
| Slovenia | ~710 | ~710 | Available |
| South Africa | ~1,290 | ~1,290 | Available |
| Spain | ~1,480 | ~1,490 | Available |
| UK (EA) | — | — | Pending — coverage gap |
| UK (NRFA) | — | — | Pending — coverage gap |
| USA | ~23,860 | ~23,700 | Available |

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
