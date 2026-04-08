"""
Download historical POI snapshots using Overpass API date: parameter.

This script fetches POI data from OpenStreetMap at specific points in time,
allowing analysis of urban function evolution over years.

Usage:
    python utils/download_historical_pois.py

Output:
    data/historical_pois_YYYY.csv
"""

import argparse
import csv
import json
import urllib.request
import time
from pathlib import Path
from collections import Counter

# === Config ===
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_FALLBACK = "https://overpass.kumi.systems/api/interpreter"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORICAL_DIR = DATA_DIR / "historical_pois"

MAX_RETRIES = 3
RETRY_DELAY = 15
REQUEST_DELAY = 10

# Singapore bounding box
SG_BBOX = (1.16, 103.60, 1.47, 104.08)

# 4 sub-regions to avoid timeout
SUB_REGIONS = {
    "northwest": (1.16, 103.60, 1.32, 103.84),
    "northeast": (1.32, 103.60, 1.47, 103.84),
    "southwest": (1.16, 103.84, 1.32, 104.08),
    "southeast": (1.32, 103.84, 1.47, 104.08),
}

# POI keys (same as download_pois.py)
POI_KEYS = [
    "amenity", "shop", "leisure", "tourism",
    "office", "healthcare", "craft", "historic"
]

# Output CSV columns
CSV_COLUMNS = [
    "osm_id", "osm_type", "lat", "lon",
    "amenity", "shop", "leisure", "tourism",
    "office", "healthcare", "craft", "historic",
    "name", "snapshot_date"
]

# Historical snapshot dates (selected based on ohsome analysis)
SNAPSHOT_DATES = [
    "2020-01-01T00:00:00Z",  # Baseline (pre-COVID)
    "2021-01-01T00:00:00Z",  # COVID year
    "2022-01-01T00:00:00Z",  # Recovery period
    "2023-01-01T00:00:00Z",  # Post-COVID
    "2024-01-01T00:00:00Z",  # Recent
    # Note: 2025-2026 data may be incomplete, use current data instead
]


def overpass_query(query: str, label: str) -> dict:
    """Query Overpass API with date: parameter."""
    endpoints = [OVERPASS_URL, OVERPASS_FALLBACK]

    for endpoint in endpoints:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                payload = f"[out:json][timeout:300];{query}".encode("utf-8")
                req = urllib.request.Request(
                    endpoint,
                    data=payload,
                    headers={"User-Agent": "NUS-AR5302-Project/1.0"},
                )
                with urllib.request.urlopen(req, timeout=300) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                ep_label = endpoint.split("//")[1].split("/")[0]
                print(f"  [{label}] {ep_label} attempt {attempt}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES:
                    print(f"    Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    break

    raise RuntimeError(f"All endpoints failed for: {label}")


def query_region_historical(region_name: str, bbox: tuple, snapshot_date: str) -> list:
    """Query all POIs in a region at a specific point in time."""
    s, w, n, e = bbox
    print(f"\n  Querying {region_name} at {snapshot_date[:10]}...")

    # Build Overpass query with date: parameter
    key_clauses = []
    for key in POI_KEYS:
        key_clauses.append(f'node["{key}"]({s},{w},{n},{e});')
        key_clauses.append(f'way["{key}"]({s},{w},{n},{e});')

    query = f"[out:json][date:\"{snapshot_date}\"];({''.join(key_clauses)});out center;]"

    result = overpass_query(query, f"{region_name}_{snapshot_date[:10]}")
    elements = result.get("elements", [])

    print(f"    Raw elements: {len(elements)}")

    # Extract POI records
    records = []
    for el in elements:
        # Get coordinates
        if el["type"] == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        elif el["type"] == "way":
            center = el.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
        else:
            continue

        if lat is None or lon is None:
            continue

        # Get tags
        tags = el.get("tags", {})

        # Build record
        record = {
            "osm_id": el.get("id"),
            "osm_type": el["type"],
            "lat": lat,
            "lon": lon,
            "amenity": tags.get("amenity", ""),
            "shop": tags.get("shop", ""),
            "leisure": tags.get("leisure", ""),
            "tourism": tags.get("tourism", ""),
            "office": tags.get("office", ""),
            "healthcare": tags.get("healthcare", ""),
            "craft": tags.get("craft", ""),
            "historic": tags.get("historic", ""),
            "name": tags.get("name", ""),
            "snapshot_date": snapshot_date[:10]
        }
        records.append(record)

    print(f"    Valid POI records: {len(records)}")
    return records


def download_snapshot(snapshot_date: str) -> int:
    """Download POI data for a specific snapshot date."""
    date_str = snapshot_date[:10]
    print(f"\n{'='*60}")
    print(f"Downloading snapshot: {date_str}")
    print(f"{'='*60}")

    all_records = []

    for region_name, bbox in SUB_REGIONS.items():
        records = query_region_historical(region_name, bbox, snapshot_date)
        all_records.extend(records)

        # Rate limiting between sub-regions
        if region_name != list(SUB_REGIONS.keys())[-1]:
            print(f"    Waiting {REQUEST_DELAY}s before next region...")
            time.sleep(REQUEST_DELAY)

    # Deduplicate
    seen = {}
    for r in all_records:
        oid = r["osm_id"]
        if oid not in seen:
            seen[oid] = r
        else:
            # Keep the one with more tags
            existing_keys = sum(1 for k in POI_KEYS if seen[oid][k])
            new_keys = sum(1 for k in POI_KEYS if r[k])
            if new_keys > existing_keys:
                seen[oid] = r

    final_records = list(seen.values())
    print(f"\n  After deduplication: {len(final_records)} POIs")

    # Save to CSV
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    output_path = HISTORICAL_DIR / f"historical_pois_{date_str}.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(final_records)

    size_kb = output_path.stat().st_size / 1024
    print(f"\n  Saved: {output_path} ({len(final_records)} records, {size_kb:.1f} KB)")

    return len(final_records)


def main():
    """Main execution."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Download historical POI snapshots")
    parser.add_argument("--years", type=int, nargs="+", default=[2020, 2022, 2024],
                       help="Years to download (default: 2020 2022 2024)")
    parser.add_argument("--test", action="store_true", help="Test mode: only one region")
    args = parser.parse_args()

    print("="*60)
    print("Historical POI Snapshot Download")
    print("="*60)

    # Generate snapshot dates for requested years
    dates_to_download = [f"{year}-01-01T00:00:00Z" for year in args.years]

    print(f"\nSnapshots to download: {[d[:10] for d in dates_to_download]}")
    print(f"Total: {len(dates_to_download)} snapshots")

    # Download each snapshot
    results = {}
    for snapshot_date in dates_to_download:
        try:
            count = download_snapshot(snapshot_date)
            results[snapshot_date[:10]] = count
        except Exception as e:
            print(f"\n  ERROR: Failed to download {snapshot_date[:10]}: {e}")
            results[snapshot_date[:10]] = None

        # Delay between snapshots
        if snapshot_date != dates_to_download[-1]:
            print(f"\n  Waiting 30s before next snapshot...")
            time.sleep(30)

    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)

    for date, count in results.items():
        if count is not None:
            print(f"  {date}: {count:,} POIs")
        else:
            print(f"  {date}: FAILED")

    print(f"\nData saved to: {HISTORICAL_DIR}/")
    print("\nNext steps:")
    print("1. Run LDA on each snapshot")
    print("2. Compare topic distributions over time")
    print("3. Cross-reference with ohsome quality data")


if __name__ == "__main__":
    main()
