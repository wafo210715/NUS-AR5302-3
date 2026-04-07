"""
Explore POI metadata from OpenStreetMap via Overpass API.

Queries a small area of Singapore to understand:
1. What POI tags exist (amenity, shop, leisure, etc.)
2. What temporal metadata is available (opening_hours, created, check_date, etc.)
3. What lifecycle/quality metadata exists (version, timestamp, etc.)
4. How many POIs we can expect per area

Uses overpass.kumi.systems (the endpoint that worked for Part 1).
"""

import json
import time
import urllib.request
from collections import Counter
from math import cos, radians
from pathlib import Path

# === Config ===
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MAX_RETRIES = 3
RETRY_DELAY = 15

# Small bbox around Orchard area (dense POI zone) for testing
# Format: south, west, north, east
ORCHARD_BBOX = (1.2980, 103.8280, 1.3080, 103.8420)

# POI keys to query
POI_KEYS = [
    "amenity", "shop", "leisure", "tourism",
    "office", "healthcare", "craft", "historic"
]


def overpass_query(query: str, label: str) -> dict:
    """Query Overpass API with retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            payload = f"[out:json][timeout:120];{query}".encode("utf-8")
            req = urllib.request.Request(
                OVERPASS_URL,
                data=payload,
                headers={"User-Agent": "NUS-AR5302-Project/1.0"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [{label}] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def explore_pois():
    """Query POIs in Orchard area and analyze their metadata."""
    s, w, n, e = ORCHARD_BBOX
    print(f"Querying POIs in Orchard area: ({s},{w},{n},{e})")
    print(f"  ~{(n-s)*111:.1f} km x {(e-w)*111*cos(radians(s)):.1f} km\n")

    # Build Overpass query for all POI keys
    key_clauses = []
    for key in POI_KEYS:
        key_clauses.append(f'node["{key}"]({s},{w},{n},{e});')
        key_clauses.append(f'way["{key}"]({s},{w},{n},{e});')

    query = f"({''.join(key_clauses)});out center meta;"

    result = overpass_query(query, "POI exploration")
    elements = result.get("elements", [])

    print(f"Total elements returned: {len(elements)}\n")

    # --- Analyze element types ---
    type_counts = Counter(el["type"] for el in elements)
    print("Element types:")
    for t, c in type_counts.most_common():
        print(f"  {t}: {c}")

    # --- Analyze POI keys (primary classification) ---
    primary_key_counts = Counter()
    for el in elements:
        tags = el.get("tags", {})
        for key in POI_KEYS:
            if key in tags:
                primary_key_counts[key] += 1
                break  # count each element once by priority

    print(f"\nPOI key distribution (by priority {POI_KEYS}):")
    for key, count in primary_key_counts.most_common():
        print(f"  {key}: {count}")

    # --- Analyze tag value diversity per key ---
    print(f"\nTag value diversity per key:")
    key_value_counts = {}
    for key in POI_KEYS:
        values = []
        for el in elements:
            tags = el.get("tags", {})
            if key in tags:
                values.append(tags[key])
        key_value_counts[key] = Counter(values)
        unique = len(set(values))
        print(f"  {key}: {len(values)} POIs, {unique} unique values")
        if unique <= 15:
            for v, c in key_value_counts[key].most_common(15):
                print(f"    {v}: {c}")

    # --- Analyze temporal/lifecycle metadata ---
    temporal_tags = [
        "opening_hours", "opening_hours:covid19",
        "check_date", "check_date:opening_hours",
        "start_date", "end_date", "description",
        "created", "created_by",
        "website", "phone", "contact:website", "contact:phone",
        "brand", "operator", "name", "name:en", "name:zh",
        "wheelchair", "internet_access",
        "addr:housenumber", "addr:street", "addr:postcode",
        "building", "building:levels",
        "layer", "level", "indoor",
        "fee", "payment", "currency",
        "smoking", "diet", "cuisine",
        "capacity", "seats", "sport", "surface",
    ]

    print(f"\nTemporal & quality metadata coverage:")
    for tag in temporal_tags:
        count = sum(1 for el in elements if tag in el.get("tags", {}))
        pct = count / len(elements) * 100 if elements else 0
        if count > 0:
            # Show sample values
            samples = set()
            for el in elements:
                if tag in el.get("tags", {}):
                    samples.add(el["tags"][tag][:80])
                    if len(samples) >= 3:
                        break
            sample_str = " | ".join(samples)
            print(f"  {tag}: {count} ({pct:.1f}%)  e.g. {sample_str}")

    # --- OSM element metadata (version, timestamp, changeset) ---
    print(f"\nOSM element metadata:")
    has_version = sum(1 for el in elements if "version" in el)
    has_timestamp = sum(1 for el in elements if "timestamp" in el)
    has_changeset = sum(1 for el in elements if "changeset" in el)
    has_uid = sum(1 for el in elements if "uid" in el)
    has_user = sum(1 for el in elements if "user" in el)
    print(f"  version: {has_version}/{len(elements)}")
    print(f"  timestamp (last edit): {has_timestamp}/{len(elements)}")
    print(f"  changeset: {has_changeset}/{len(elements)}")
    print(f"  uid: {has_uid}/{len(elements)}")

    # Show timestamp range
    timestamps = [el["timestamp"] for el in elements if "timestamp" in el]
    if timestamps:
        timestamps.sort()
        print(f"  timestamp range: {timestamps[0]} to {timestamps[-1]}")

    # Version distribution
    versions = Counter(el.get("version", 0) for el in elements)
    print(f"  version distribution:")
    for v in sorted(versions.keys())[:10]:
        print(f"    v{v}: {versions[v]}")

    # --- Show a few complete examples ---
    print(f"\n{'='*60}")
    print("EXAMPLE POIs (first 3 with amenity tag):")
    print(f"{'='*60}")
    shown = 0
    for el in elements:
        tags = el.get("tags", {})
        if "amenity" in tags and shown < 3:
            print(f"\nOSM ID: {el['id']} (type={el['type']}, version={el.get('version')})")
            print(f"  timestamp: {el.get('timestamp')}")
            print(f"  coordinates: {el.get('lat')}, {el.get('lon')}")
            if el["type"] == "way":
                center = el.get("center", {})
                print(f"  center: {center.get('lat')}, {center.get('lon')}")
            print(f"  tags:")
            for k, v in sorted(tags.items()):
                print(f"    {k} = {v}")
            shown += 1

    # --- Save raw response for inspection ---
    out_path = Path("data/poi_exploration_raw.json")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nRaw response saved to {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    print("=" * 60)
    print("POI Metadata Exploration (Overpass API)")
    print("=" * 60)
    print()
    explore_pois()
    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)
