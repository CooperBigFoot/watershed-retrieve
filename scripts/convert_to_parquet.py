from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import NamedTuple

import geopandas as gpd

LAYERS = ["watersheds", "rivers"]

DEFAULT_INPUT_DIR = Path(
    os.environ.get("WATERSHED_EXTRACT_INPUT_DIR", "/Users/nicolaslazaro/Desktop/watershed-extract-v2/output")
)
DEFAULT_OUTPUT_DIR = Path(
    os.environ.get("WATERSHED_EXTRACT_OUTPUT_DIR", "/Users/nicolaslazaro/Desktop/watershed-extract-v2/output_parquet")
)


class RegionSpec(NamedTuple):
    key: str
    output_name: str


REGIONS: list[RegionSpec] = [
    RegionSpec("australia", "australia"),
    RegionSpec("brazil", "brazil"),
    RegionSpec("canada", "canada"),
    RegionSpec("chile", "chile"),
    RegionSpec("czech", "czech"),
    RegionSpec("france", "france"),
    RegionSpec("germany", "germany"),
    RegionSpec("japan", "japan"),
    RegionSpec("lithuania", "lithuania"),
    RegionSpec("norway", "norway"),
    RegionSpec("poland", "poland"),
    RegionSpec("portugal", "portugal"),
    RegionSpec("slovenia", "slovenia"),
    RegionSpec("south_africa", "south_africa"),
    RegionSpec("spain", "spain"),
    RegionSpec("uk_ea", "uk_ea"),
    RegionSpec("uk_nrfa", "uk_nrfa"),
    RegionSpec("usa", "usa"),
]


def gpkg_path(input_dir: Path, region: RegionSpec) -> Path:
    return input_dir / f"REGION_NAME={region.key}" / "data_type=gpkg" / f"{region.key}.gpkg"


def sort_key(input_dir: Path, region: RegionSpec) -> int:
    path = gpkg_path(input_dir, region)
    return path.stat().st_size if path.exists() else 2**63


def convert(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    ordered = sorted(REGIONS, key=lambda r: sort_key(input_dir, r))
    size_report: list[tuple[str, str, int, int, int, float]] = []

    for region in ordered:
        path = gpkg_path(input_dir, region)
        if not path.exists():
            print(f"SKIP {region.key}: gpkg not found at {path}")
            continue

        gpkg_size = path.stat().st_size

        for layer in LAYERS:
            parquet_path = output_dir / f"{region.output_name}_{layer}.parquet"

            if parquet_path.exists():
                print(f"SKIP {region.output_name}_{layer}.parquet (already exists)")
                pq_size = parquet_path.stat().st_size
                gdf = gpd.read_parquet(parquet_path, columns=["geometry"])
                size_report.append((region.output_name, layer, len(gdf), gpkg_size, pq_size, 0.0))
                del gdf
                continue

            t0 = time.time()
            print(f"Reading {region.key}.gpkg layer={layer} ...", flush=True)
            gdf = gpd.read_file(path, layer=layer)
            invalid_mask = ~gdf.geometry.is_valid
            n_invalid = invalid_mask.sum()
            if n_invalid > 0:
                print(f"  Repairing {n_invalid} invalid geometries ...", flush=True)
                gdf.geometry = gdf.make_valid()
            nrows = len(gdf)

            if region.key != region.output_name and "country" in gdf.columns:
                gdf["country"] = gdf["country"].replace({region.key: region.output_name})

            print(f"  Writing {parquet_path.name} ({nrows:,} rows) ...", flush=True)
            gdf.to_parquet(parquet_path, row_group_size=1000)
            elapsed = time.time() - t0
            pq_size = parquet_path.stat().st_size

            size_report.append((region.output_name, layer, nrows, gpkg_size, pq_size, elapsed))
            print(f"  Done in {elapsed:.1f}s  gpkg={gpkg_size / 1e6:.1f}MB  parquet={pq_size / 1e6:.1f}MB")
            del gdf

    print("\n" + "=" * 90)
    print(f"{'Country':<16} {'Layer':<12} {'Rows':>10} {'GPKG (MB)':>12} {'Parquet (MB)':>14} {'Time (s)':>10}")
    print("-" * 90)
    total_gpkg = total_pq = 0
    seen_gpkg: set[str] = set()
    for out_name, layer, nrows, gpkg_b, pq_b, secs in size_report:
        gpkg_mb = gpkg_b / 1e6
        pq_mb = pq_b / 1e6
        total_pq += pq_b
        if out_name not in seen_gpkg:
            total_gpkg += gpkg_b
            seen_gpkg.add(out_name)
        print(f"{out_name:<16} {layer:<12} {nrows:>10,} {gpkg_mb:>12.1f} {pq_mb:>14.1f} {secs:>10.1f}")
    print("-" * 90)
    print(f"{'TOTAL':<16} {'':<12} {'':<10} {total_gpkg / 1e6:>12.1f} {total_pq / 1e6:>14.1f}")
    print("=" * 90)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert hydra-shed GeoPackage output files to GeoParquet.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Path to gpkg output directory (default: $WATERSHED_EXTRACT_INPUT_DIR or hardcoded fallback)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Path to parquet output directory (default: $WATERSHED_EXTRACT_OUTPUT_DIR or hardcoded fallback)",
    )
    args = parser.parse_args()
    convert(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
