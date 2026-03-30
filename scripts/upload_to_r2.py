#!/usr/bin/env python3
"""Upload parquet files to Cloudflare R2 for public CDN access."""

import argparse
import subprocess
import sys
from typing import NamedTuple

CDN_HOST = "https://pub-52975bdd539f43819da3692334f4999c.r2.dev"
R2_BUCKET = "r2:large-sample-hydrology"

COUNTRIES = [
    "australia",
    "brazil",
    "canada",
    "chile",
    "czech",
    "france",
    "germany",
    "japan",
    "lithuania",
    "norway",
    "poland",
    "portugal",
    "slovenia",
    "south_africa",
    "spain",
    "usa",
]


class FabricUploadSpec(NamedTuple):
    source_dir: str
    r2_dest: str
    cdn_base: str


_FABRICS: dict[str, FabricUploadSpec] = {
    "merit": FabricUploadSpec(
        source_dir="/Users/nicolaslazaro/Desktop/watershed-extract-v2/output_parquet",
        r2_dest=f"{R2_BUCKET}/watershed-retrieve/v1/",
        cdn_base=f"{CDN_HOST}/watershed-retrieve/v1",
    ),
    "hydrosheds-v1": FabricUploadSpec(
        source_dir="/Users/nicolaslazaro/Desktop/watershed-extract-v2/output_parquet_hydrosheds_v1",
        r2_dest=f"{R2_BUCKET}/watershed-retrieve/v1/hydrosheds-v1/",
        cdn_base=f"{CDN_HOST}/watershed-retrieve/v1/hydrosheds-v1",
    ),
}


def upload(spec: FabricUploadSpec, dry_run: bool = False) -> None:
    cmd = [
        "rclone",
        "copy",
        spec.source_dir,
        spec.r2_dest,
        "--include",
        "*.parquet",
        "--progress",
        "--checksum",
    ]
    if dry_run:
        cmd.append("--dry-run")
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def verify(spec: FabricUploadSpec) -> None:
    import urllib.request

    files = [f"{c}_{layer}.parquet" for c in COUNTRIES for layer in ["watersheds", "rivers"]]
    for f in files:
        url = f"{spec.cdn_base}/{f}"
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "watershed-retrieve"})
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"  OK {resp.status} {url}")
        except Exception as exc:
            print(f"  FAIL {url}: {exc}")
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload parquet files to R2")
    parser.add_argument(
        "--fabric",
        choices=list(_FABRICS.keys()),
        default="merit",
        help="Hydrofabric to upload (default: merit)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument("--verify-only", action="store_true", help="Only verify CDN access")
    args = parser.parse_args()

    spec = _FABRICS[args.fabric]

    if args.verify_only:
        verify(spec)
        return

    upload(spec, dry_run=args.dry_run)
    if not args.dry_run:
        print("\nVerifying CDN access...")
        verify(spec)


if __name__ == "__main__":
    main()
