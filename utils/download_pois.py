"""
Download all POIs across Singapore from OpenStreetMap via Overpass API.

Queries 8 POI keys (amenity, shop, leisure, tourism, office, healthcare,
craft, historic) and saves results to data/sg_pois_all.csv.

Strategy: Split Singapore into 4 sub-regions to avoid Overpass timeouts.

Usage:
    python utils/download_pois.py
    python utils/download_pois.py --test    # only query Orchard area
"""

import argparse
import csv
import json
import time
import urllib.request
from collections import Counter
from pathlib import Path

# === Config ===
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_FALLBACK = "https://overpass.kumi.systems/api/interpreter"
MAX_RETRIES = 3
RETRY_DELAY = 15
REQUEST_DELAY = 5  # seconds between sub-region queries

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Singapore bounding box: south, west, north, east
SG_BBOX = (1.16, 103.60, 1.47, 104.08)

# 4 sub-regions to avoid timeout (each ~0.16° × 0.24°)
SUB_REGIONS = {
    "northwest": (1.16, 103.60, 1.32, 103.84),
    "northeast": (1.32, 103.60, 1.47, 103.84),
    "southwest": (1.16, 103.84, 1.32, 104.08),
    "southeast": (1.32, 103.84, 1.47, 104.08),
}

# Small bbox for testing (Orchard area)
TEST_BBOX = (1.2980, 103.8280, 1.3080, 103.8420)

# POI keys to query
POI_KEYS = [
    "amenity", "shop", "leisure", "tourism",
    "office", "healthcare", "craft", "historic"
]

# Output CSV columns
CSV_COLUMNS = [
    "osm_id", "osm_type", "lat", "lon",
    "version", "timestamp", "changeset_id", "user_id",
    "amenity", "shop", "leisure", "tourism",
    "office", "healthcare", "craft", "historic",
    "name", "all_tags"
]


def overpass_query(query: str, label: str) -> dict:
    """Query Overpass API with retries and fallback endpoint."""
    endpoints = [OVERPASS_URL, OVERPASS_FALLBACK]

    for endpoint in endpoints:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                payload = f"[out:json][timeout:180];{query}".encode("utf-8")
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
                    break  # try next endpoint

    raise RuntimeError(f"All endpoints failed for: {label}")


def extract_poi_record(el: dict) -> dict | None:
    """Extract a POI record from an Overpass element.

    Returns None if the element has no POI keys.
    """
    tags = el.get("tags", {})

    # Check if this element has at least one POI key
    has_poi = any(key in tags for key in POI_KEYS)
    if not has_poi:
        return None

    # Coordinates: use lat/lon for nodes, center for ways
    if el["type"] == "node":
        lat = el.get("lat")
        lon = el.get("lon")
    elif el["type"] == "way":
        center = el.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
    else:
        return None  # skip relations

    if lat is None or lon is None:
        return None

    # Build record
    record = {
        "osm_id": el.get("id"),
        "osm_type": el["type"],
        "lat": lat,
        "lon": lon,
        "version": el.get("version", ""),
        "timestamp": el.get("timestamp", ""),
        "changeset_id": el.get("changeset", ""),
        "user_id": el.get("uid", ""),
        # POI key values (empty string if not present)
        "amenity": tags.get("amenity", ""),
        "shop": tags.get("shop", ""),
        "leisure": tags.get("leisure", ""),
        "tourism": tags.get("tourism", ""),
        "office": tags.get("office", ""),
        "healthcare": tags.get("healthcare", ""),
        "craft": tags.get("craft", ""),
        "historic": tags.get("historic", ""),
        "name": tags.get("name", ""),
        "all_tags": json.dumps(tags, ensure_ascii=False),
    }

    return record


def query_region(name: str, bbox: tuple) -> list:
    """Query all POIs in a bounding box region."""
    s, w, n, e = bbox
    print(f"\n  Querying {name}: ({s}, {w}, {n}, {e})")

    # Build Overpass query for all POI keys (nodes + ways)
    key_clauses = []
    for key in POI_KEYS:
        key_clauses.append(f'node["{key}"]({s},{w},{n},{e});')
        key_clauses.append(f'way["{key}"]({s},{w},{n},{e});')

    query = f"({''.join(key_clauses)});out center meta;"

    result = overpass_query(query, name)
    elements = result.get("elements", [])

    print(f"    Raw elements: {len(elements)}")

    # Extract POI records
    records = []
    for el in elements:
        record = extract_poi_record(el)
        if record is not None:
            records.append(record)

    print(f"    Valid POI records: {len(records)}")
    return records


def deduplicate(records: list) -> list:
    """Remove duplicate POIs (same osm_id, keep the one with more tags)."""
    seen = {}
    for r in records:
        oid = r["osm_id"]
        if oid not in seen:
            seen[oid] = r
        else:
            # Keep the one with more non-empty POI key fields
            existing_keys = sum(1 for k in POI_KEYS if seen[oid][k])
            new_keys = sum(1 for k in POI_KEYS if r[k])
            if new_keys > existing_keys:
                seen[oid] = r

    return list(seen.values())


def validate(records: list) -> None:
    """Print validation checks."""
    if not records:
        print("\n  WARNING: No records to validate!")
        return

    total = len(records)

    # Coordinate range check (Singapore bounds)
    lats = [r["lat"] for r in records]
    lons = [r["lon"] for r in records]
    print(f"\n  Validation:")
    print(f"    Total POIs: {total}")
    print(f"    Lat range: {min(lats):.4f} to {max(lats):.4f} (expected ~1.16-1.47)")
    print(f"    Lon range: {min(lons):.4f} to {max(lons):.4f} (expected ~103.60-104.08)")

    # POI key distribution
    key_counts = Counter()
    for r in records:
        for key in POI_KEYS:
            if r[key]:
                key_counts[key] += 1
    print(f"    POI key coverage:")
    for key, count in key_counts.most_common():
        pct = count / total * 100
        print(f"      {key}: {count} ({pct:.1f}%)")

    # Name coverage
    named = sum(1 for r in records if r["name"])
    print(f"    Named: {named}/{total} ({named/total*100:.1f}%)")

    # Type distribution
    type_counts = Counter(r["osm_type"] for r in records)
    print(f"    Types: {dict(type_counts)}")

    # Version distribution
    versions = Counter(r["version"] for r in records)
    v1_count = versions.get(1, 0)
    print(f"    Version 1 (never edited): {v1_count}/{total} ({v1_count/total*100:.1f}%)")


def save_csv(records: list, filepath: Path) -> None:
    """Save POI records to CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"\n  Saved: {filepath} ({len(records)} records, {size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Download Singapore POIs from OSM")
    parser.add_argument("--test", action="store_true", help="Only query Orchard area")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.test:
        print("=== TEST MODE: Orchard area only ===")
        regions = {"orchard_test": TEST_BBOX}
    else:
        print("=== Downloading POIs for all of Singapore ===")
        regions = SUB_REGIONS

    all_records = []

    for name, bbox in regions.items():
        records = query_region(name, bbox)
        all_records.extend(records)

        # Rate limiting between sub-region queries
        if name != list(regions.keys())[-1]:
            print(f"    Waiting {REQUEST_DELAY}s before next query...")
            time.sleep(REQUEST_DELAY)

    # Deduplicate (some POIs may appear in overlapping regions)
    print(f"\n  Deduplicating...")
    before = len(all_records)
    all_records = deduplicate(all_records)
    after = len(all_records)
    print(f"    Removed {before - after} duplicates ({before} → {after})")

    # Validate
    validate(all_records)

    # Save
    out_path = DATA_DIR / "sg_pois_all.csv"
    save_csv(all_records, out_path)

    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
