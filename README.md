# watershed-retrieve

Instant access to ~58,000 pre-delineated MERIT-Hydro watershed boundaries and river networks across 15 countries, stored as GeoParquet files.

## Setup

```bash
# Install
uv sync

# Configure data directory (default: ./data)
export WATERSHED_RETRIEVE_DATA_DIR=/path/to/parquet/files
```

The data directory should contain GeoParquet files named `{country}_watersheds.parquet` and `{country}_rivers.parquet`.

## API

```python
import watershed_retrieve as wr
```

### Configuration

```python
# Option 1: Environment variable
# export WATERSHED_RETRIEVE_DATA_DIR=/path/to/data

# Option 2: Programmatic
wr.configure("/path/to/data")
```

### Discovery

```python
# List all supported countries
wr.available_countries()
# -> ['australia', 'brazil', 'canada', 'chile', 'czech', 'france',
#     'germany', 'japan', 'lithuania', 'norway', 'poland', 'portugal',
#     'slovenia', 'south_africa', 'usa']

# List gauge IDs for a country
wr.available_gauges("portugal")
# -> ['02G-02H', '02O-01H', ..., '16J-01H']  (73 gauges)
```

### Single watershed

```python
# Get watershed boundary (returns GeoDataFrame, 1 row)
gdf = wr.get_watershed("portugal", "04K/04A")

# Get watershed + river network (returns WatershedResult NamedTuple)
result = wr.get_watershed_with_rivers("portugal", "04K/04A")
watershed, rivers = result  # unpackable
```

### Bulk retrieval

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

### Gauge ID normalization

Slashes are automatically normalized to dashes. Both forms work:

```python
wr.get_watershed("portugal", "04K/04A")   # slash
wr.get_watershed("portugal", "04K-04A")   # dash — equivalent
```

### Errors

```python
from watershed_retrieve import (
    CountryNotFoundError,   # invalid country name
    GaugeNotFoundError,     # gauge ID not in dataset
    DataNotFoundError,      # parquet file missing from data_dir
)
```

All inherit from `WatershedRetrieveError`.

## Supported countries

| Country | Gauges |
|---------|--------|
| Australia | ~5,200 |
| Brazil | ~4,300 |
| Canada | ~5,800 |
| Chile | ~500 |
| Czech Republic | ~400 |
| France | ~5,400 |
| Germany | ~500 |
| Japan | ~1,200 |
| Lithuania | ~70 |
| Norway | ~600 |
| Poland | ~600 |
| Portugal | 73 |
| Slovenia | ~200 |
| South Africa | ~900 |
| USA | ~32,000 |

## Development

```bash
# Run tests (requires data directory)
WATERSHED_RETRIEVE_DATA_DIR=/path/to/data uv run pytest tests/ -v

# Lint & format
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```
