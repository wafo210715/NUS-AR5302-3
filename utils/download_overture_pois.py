"""
Download Overture Maps POI data for Singapore from Source Cooperative.

Uses s3fs to discover files and download them to a temp directory,
then DuckDB to filter for Singapore's bounding box.

Outputs (saved to data/overture_pois/):
  - overture_sg_{release}.parquet  — filtered POI data (GeoParquet)
  - overture_sg_{release}.csv      — backup CSV copy

Usage:
    python utils/download_overture_pois.py
    python utils/download_overture_pois.py --release 2025-12-17-0
    python utils/download_overture_pois.py --list-releases
"""

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "overture_pois"

# Singapore bounding box (WGS84)
SG_LAT_MIN, SG_LAT_MAX = 1.15, 1.48
SG_LON_MIN, SG_LON_MAX = 103.60, 104.08

# Source Cooperative S3 path for Overture Places
S3_BUCKET = "us-west-2.opendata.source.coop"
S3_PREFIX_TEMPLATE = "fused/overture/{release}/theme=places/type=place"

# Default release: Dec 2025 snapshot
DEFAULT_RELEASE = "2025-12-17-0"


def discover_parquet_files(release: str) -> list:
    """Use s3fs to list all parquet files in the S3 directory."""
    import s3fs

    fs = s3fs.S3FileSystem(anon=True, client_kwargs={"region_name": "us-west-2"})
    prefix = S3_PREFIX_TEMPLATE.format(release=release)
    s3_dir = f"s3://{S3_BUCKET}/{prefix}/"

    print(f"  Discovering parquet files on S3...")
    files = fs.ls(s3_dir)
    s3_paths = [f"s3://{f}" for f in files if f.endswith(".parquet")]

    print(f"  Found {len(s3_paths)} parquet files")
    return s3_paths


def download_files_locally(s3_paths: list, temp_dir: Path) -> list:
    """Download S3 parquet files to a local temp directory."""
    import s3fs

    fs = s3fs.S3FileSystem(anon=True, client_kwargs={"region_name": "us-west-2"})
    local_paths = []

    total = len(s3_paths)
    for i, s3_path in enumerate(s3_paths):
        filename = Path(s3_path).name
        local_path = temp_dir / filename
        print(f"  [{i+1}/{total}] Downloading {filename}...", end=" ", flush=True)

        start = time.time()
        fs.get(s3_path, str(local_path))
        elapsed = time.time() - start

        size_mb = local_path.stat().st_size / (1024 * 1024)
        print(f"{size_mb:.0f} MB ({elapsed:.1f}s)")
        local_paths.append(local_path)

    return local_paths


def filter_with_duckdb(
    local_paths: list,
    output_parquet: Path,
    output_csv: Path,
) -> bool:
    """Use DuckDB to filter POIs for Singapore bbox from local parquet files."""
    import duckdb

    # Use glob pattern for local parquet files (DuckDB handles this natively)
    temp_dir = str(local_paths[0].parent).replace("\\", "/")
    glob_pattern = f"{temp_dir}/*.parquet"

    output_parquet_str = str(output_parquet).replace("\\", "/")

    conn = duckdb.connect()

    # Load spatial extension for geometry functions
    conn.execute("INSTALL spatial;")
    conn.execute("LOAD spatial;")

    # Count POIs in bbox
    count_sql = f"""
    SELECT COUNT(*) AS total
    FROM read_parquet('{glob_pattern}')
    WHERE operating_status = 'open'
      AND bbox.xmin BETWEEN {SG_LON_MIN} AND {SG_LON_MAX}
      AND bbox.ymin BETWEEN {SG_LAT_MIN} AND {SG_LAT_MAX}
      AND bbox.xmax BETWEEN {SG_LON_MIN} AND {SG_LON_MAX}
      AND bbox.ymax BETWEEN {SG_LAT_MIN} AND {SG_LAT_MAX}
    """

    print(f"\n  Filtering POIs for Singapore bbox...")
    start = time.time()
    total = conn.execute(count_sql).fetchone()[0]
    elapsed = time.time() - start
    print(f"  Found {total:,} POIs (took {elapsed:.1f}s)")

    if total == 0:
        print("  WARNING: No POIs found! Check release name and bbox.")
        conn.close()
        return False

    # Export filtered data to Parquet
    export_sql = f"""
    COPY (
        SELECT
            id,
            names.primary AS name,
            categories.primary AS category,
            confidence,
            operating_status,
            bbox.xmin AS lon_min,
            bbox.ymin AS lat_min,
            bbox.xmax AS lon_max,
            bbox.ymax AS lat_max,
            ST_AsText(geometry) AS geometry_wkt
        FROM read_parquet('{glob_pattern}')
        WHERE operating_status = 'open'
          AND bbox.xmin BETWEEN {SG_LON_MIN} AND {SG_LON_MAX}
          AND bbox.ymin BETWEEN {SG_LAT_MIN} AND {SG_LAT_MAX}
          AND bbox.xmax BETWEEN {SG_LON_MIN} AND {SG_LON_MAX}
          AND bbox.ymax BETWEEN {SG_LAT_MIN} AND {SG_LAT_MAX}
    ) TO '{output_parquet_str}' (FORMAT PARQUET);
    """

    print(f"  Exporting to Parquet...")
    start = time.time()
    conn.execute(export_sql)
    elapsed = time.time() - start
    size_mb = output_parquet.stat().st_size / (1024 * 1024)
    print(f"  Saved Parquet ({size_mb:.1f} MB, {elapsed:.1f}s)")

    # Export CSV backup
    print(f"  Exporting CSV backup...")
    df = conn.execute(f"""
        SELECT
            id,
            name,
            category,
            confidence,
            operating_status,
            lon_min, lat_min, lon_max, lat_max
        FROM read_parquet('{output_parquet_str}')
        ORDER BY category, name
    """).df()

    df.to_csv(output_csv, index=False)
    csv_size_kb = output_csv.stat().st_size / 1024
    print(f"  Saved CSV ({len(df):,} rows, {csv_size_kb:.0f} KB)")

    conn.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Download Overture POI data for Singapore")
    parser.add_argument(
        "--release",
        default=DEFAULT_RELEASE,
        help=f"Overture release tag (default: {DEFAULT_RELEASE})"
    )
    parser.add_argument(
        "--list-releases",
        action="store_true",
        help="List available releases on Source Cooperative and exit"
    )
    args = parser.parse_args()

    if args.list_releases:
        import s3fs
        print("Discovering available releases on Source Cooperative...\n")
        fs = s3fs.S3FileSystem(anon=True, client_kwargs={"region_name": "us-west-2"})
        prefix = "fused/overture/"
        dirs = fs.ls(f"s3://{S3_BUCKET}/{prefix}")
        releases = sorted(
            d.split("/")[-1]
            for d in dirs
            if d.startswith(f"{S3_BUCKET}/{prefix}") and d.count("/") == prefix.count("/") + 1
        )
        print(f"  Found {len(releases)} releases:")
        for r in releases:
            print(f"    {r}")
        print(f"\n  Default (this script): {DEFAULT_RELEASE}")
        return

    release = args.release

    print("=" * 60)
    print("Overture Maps POI Download — Singapore")
    print("=" * 60)
    print(f"  Release: {release}")
    print(f"  Output dir: {DATA_DIR}")
    print(f"  BBox: lat [{SG_LAT_MIN}, {SG_LAT_MAX}], lon [{SG_LON_MIN}, {SG_LON_MAX}]")

    # Create output directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Output file paths
    parquet_name = f"overture_sg_{release}.parquet"
    csv_name = f"overture_sg_{release}.csv"
    output_parquet = DATA_DIR / parquet_name
    output_csv = DATA_DIR / csv_name

    # Check if already downloaded
    if output_parquet.exists():
        size_mb = output_parquet.stat().st_size / (1024 * 1024)
        print(f"\n  File already exists: {output_parquet.name}")
        print(f"  Size: {size_mb:.1f} MB")
        response = input("  Re-download? (y/N): ").strip().lower()
        if response != "y":
            print("  Skipping download.")
            return

    # Step 1: Discover files on S3
    print()
    s3_paths = discover_parquet_files(release)

    if not s3_paths:
        print(f"\n  ERROR: No parquet files found for release '{release}'")
        print(f"  Check available releases with: --list-releases")
        sys.exit(1)

    # Step 2: Download to temp directory
    temp_dir = Path(tempfile.mkdtemp(prefix="overture_sg_"))
    print(f"\n  Temp dir: {temp_dir}")
    print()
    local_paths = download_files_locally(s3_paths, temp_dir)

    # Step 3: Filter with DuckDB
    print()
    success = filter_with_duckdb(local_paths, output_parquet, output_csv)

    # Clean up temp directory
    print(f"\n  Cleaning up temp directory...")
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"  Removed {temp_dir}")

    if success:
        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)
        for f in [output_parquet, output_csv]:
            if f.exists():
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  {f.name} ({size_mb:.1f} MB)")
        print("=" * 60)
    else:
        print("\n  Download failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
