from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import NamedTuple

import pandas as pd
from pyproj import Transformer

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DatasetSpec(NamedTuple):
    filename: str
    region: str
    id_prefix: str
    lat_col: str
    lon_col: str
    source_crs: str | None


class Outlet(NamedTuple):
    id: str
    lat: float
    lon: float
    region: str


DATASETS: list[DatasetSpec] = [
    DatasetSpec("australia_sites.csv", "australia", "australia_", "latitude", "longitude", None),
    DatasetSpec("brazil_sites.csv", "brazil", "brazil_", "latitude", "longitude", None),
    DatasetSpec("canada_sites.csv", "canada", "canada_", "latitude", "longitude", None),
    DatasetSpec("chile_sites.csv", "chile", "chile_", "latitude", "longitude", None),
    DatasetSpec("czech_sites.csv", "czech", "czech_", "latitude", "longitude", None),
    DatasetSpec("french_sites.csv", "france", "france_", "latitude", "longitude", None),
    DatasetSpec("germany_berlin_sites.csv", "germany", "germany_berlin_", "latitude", "longitude", None),
    DatasetSpec("japan_sites.csv", "japan", "japan_", "latitude", "longitude", None),
    DatasetSpec("lithuania_sites.csv", "lithuania", "lithuania_", "latitude", "longitude", None),
    DatasetSpec("norway_sites.csv", "norway", "norway_", "latitude", "longitude", None),
    DatasetSpec("poland_sites.csv", "poland", "poland_", "latitude", "longitude", None),
    DatasetSpec("portugal_sites.csv", "portugal", "portugal_", "latitude", "longitude", None),
    DatasetSpec("slovenia_sites.csv", "slovenia", "slovenia_", "latitude", "longitude", None),
    DatasetSpec("southAfrican_sites.csv", "south_africa", "south_africa_", "latitude", "longitude", None),
    DatasetSpec("spain_sites.csv", "spain", "spain_", "COORD_UTMY_H30_ETRS89", "COORD_UTMX_H30_ETRS89", "EPSG:25830"),
    DatasetSpec("uk_ea_sites.csv", "uk_ea", "uk_ea_", "latitude", "longitude", None),
    DatasetSpec("uk_nrfa_sites.csv", "uk_nrfa", "uk_nrfa_", "latitude", "longitude", None),
    DatasetSpec("usa_sites.csv", "usa", "usa_", "latitude", "longitude", None),
]


def normalize_gauge_id(raw: str) -> str:
    return raw.strip().replace("/", "-")


def reproject_to_wgs84(easting: float, northing: float, source_crs: str) -> tuple[float, float]:
    transformer = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(easting, northing)
    return lat, lon


def load_dataset(csv_path: Path, spec: DatasetSpec) -> list[Outlet]:
    df = pd.read_csv(csv_path)

    missing_cols = {spec.lat_col, spec.lon_col, "gauge_id"} - set(df.columns)
    if missing_cols:
        logger.warning("Skipping %s — missing columns: %s", spec.filename, missing_cols)
        return []

    before = len(df)
    df = df.dropna(subset=["gauge_id", spec.lat_col, spec.lon_col])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with NaN in %s", dropped, spec.filename)

    df[spec.lat_col] = pd.to_numeric(df[spec.lat_col], errors="coerce")
    df[spec.lon_col] = pd.to_numeric(df[spec.lon_col], errors="coerce")
    before_numeric = len(df)
    df = df.dropna(subset=[spec.lat_col, spec.lon_col])
    numeric_dropped = before_numeric - len(df)
    if numeric_dropped:
        logger.warning("Dropped %d rows with non-numeric coords in %s", numeric_dropped, spec.filename)

    outlets: list[Outlet] = []
    for row in df.itertuples(index=False):
        raw_id = str(row.gauge_id)
        outlet_id = f"{spec.id_prefix}{normalize_gauge_id(raw_id)}"

        raw_lat = float(getattr(row, spec.lat_col))
        raw_lon = float(getattr(row, spec.lon_col))

        if spec.source_crs is not None:
            lat, lon = reproject_to_wgs84(raw_lon, raw_lat, spec.source_crs)
        else:
            lat, lon = raw_lat, raw_lon

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            logger.warning("Out-of-range coords for %s: lat=%s lon=%s — skipping", outlet_id, lat, lon)
            continue

        outlets.append(Outlet(id=outlet_id, lat=lat, lon=lon, region=spec.region))

    return outlets


def collect_outlets(csv_dir: Path) -> tuple[dict[str, Outlet], dict[str, int]]:
    seen: dict[str, Outlet] = {}
    counts: dict[str, int] = {}

    for spec in DATASETS:
        csv_path = csv_dir / spec.filename
        if not csv_path.exists():
            logger.warning("CSV not found: %s", csv_path)
            continue

        outlets = load_dataset(csv_path, spec)
        region_count = 0

        for outlet in outlets:
            if outlet.id not in seen:
                seen[outlet.id] = outlet
                region_count += 1

        counts[spec.region] = region_count

    return seen, counts


def render_toml(outlets: dict[str, Outlet], output_dir: str) -> str:
    lines: list[str] = [
        "[settings]",
        f'output = "{output_dir}"',
        'format = "gpkg"',
        "high_res = true",
        "rivers = true",
        "auto_download = true",
        "fill_threshold = 0",
        "max_basins_loaded = 10",
        "",
    ]

    for outlet in outlets.values():
        lines += [
            "[[outlets]]",
            f'id = "{outlet.id}"',
            f"lat = {outlet.lat}",
            f"lon = {outlet.lon}",
            f'region = "{outlet.region}"',
            "",
        ]

    return "\n".join(lines)


def print_summary(counts: dict[str, int]) -> None:
    col_width = 20
    separator = "\u2500" * (col_width + 10)
    print(f"\n{'Region':<{col_width}} {'Outlets':>8}")
    print(separator)
    total = 0
    for region, count in counts.items():
        print(f"{region:<{col_width}} {count:>8,}")
        total += count
    print(separator)
    print(f"{'TOTAL':<{col_width}} {total:>8,}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate outlets.toml for hydra-shed batch delineation.")
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=Path("/Users/nicolaslazaro/Desktop/thirdparty/RivRetrieve-Python/rivretrieve/cached_site_data/"),
        help="Directory containing RivRetrieve CSVs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outlets.toml"),
        help="Output TOML path",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/Users/nicolaslazaro/Desktop/watershed-extract-v2/output",
        help="hydra-shed output directory for [settings]",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    outlets, counts = collect_outlets(args.csv_dir)

    total = sum(counts.values())
    if total <= 70_000:
        logger.warning("Total outlet count %d is unexpectedly low (expected > 70,000)", total)

    toml_content = render_toml(outlets, args.output_dir)
    args.output.write_text(toml_content, encoding="utf-8")

    print(f"Written {total:,} outlets to {args.output}")
    print_summary(counts)


if __name__ == "__main__":
    main()
