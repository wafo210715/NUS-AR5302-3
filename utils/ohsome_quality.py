"""
Query ohsome REST API for aggregate OSM data quality metrics.

Provides temporal context for interpreting POI data quality:
  - POI count growth over time (is the dataset growing?)
  - Unique mapper activity (healthy mapping community?)
  - Edit type breakdown (creation vs modification vs deletion)

Output: data/ohsome_quality_results.json

Usage:
    python utils/ohsome_quality.py
"""

import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

# === Config ===
OHSOME_BASE = "https://api.ohsome.org/v1"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Singapore bounding box (ohsome uses: west,south,east,north)
SG_BBOX = "103.60,1.16,104.08,1.47"

# Time range: monthly from 2020-01 to 2026-02
# Note: ohsome data ends at ~2026-02-19; requesting beyond that returns 404
TIME_RANGE = "2020-01-01/2026-02-01/P1M"

# POI filter (same 8 keys as download_pois.py)
POI_FILTER = "amenity=* or shop=* or leisure=* or tourism=* or office=* or healthcare=* or craft=* or historic=*"

HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

MAX_RETRIES = 3
RETRY_DELAY = 10


def ohsome_post(endpoint: str, body: dict, label: str) -> dict:
    """POST to ohsome API with retries."""
    url = f"{OHSOME_BASE}{endpoint}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            payload = urllib.parse.urlencode(body).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [{label}] Attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                print(f"    Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise

    raise RuntimeError(f"Failed: {label}")


def query_poi_count() -> dict:
    """Query A: Total POI count over time."""
    print("\n[Query A] POI count over time...")
    body = {
        "filter": POI_FILTER,
        "bboxes": SG_BBOX,
        "time": TIME_RANGE,
    }
    result = ohsome_post("/elements/count", body, "POI count")

    # Parse result
    if "result" in result:
        values = result["result"]
        print(f"    {len(values)} time points returned")
        if values:
            first = values[0]
            last = values[-1]
            t1 = first.get("timestamp", first.get("time", ""))
            t2 = last.get("timestamp", last.get("time", ""))
            print(f"    First: {t1[:10] if t1 else '?'} → {first.get('value'):,} POIs")
            print(f"    Last:  {t2[:10] if t2 else '?'} → {last.get('value'):,} POIs")

    return result


def query_user_count() -> dict:
    """Query B: Unique mapper count over time."""
    print("\n[Query B] Unique mapper count over time...")
    body = {
        "filter": POI_FILTER,
        "bboxes": SG_BBOX,
        "time": TIME_RANGE,
    }
    result = ohsome_post("/users/count", body, "User count")

    if "result" in result:
        values = result["result"]
        print(f"    {len(values)} time points returned")
        if values:
            first = values[0]
            last = values[-1]
            t1 = first.get("timestamp", first.get("time", ""))
            t2 = last.get("timestamp", last.get("time", ""))
            print(f"    First: {t1[:10] if t1 else '?'} → {first.get('value'):,} mappers")
            print(f"    Last:  {t2[:10] if t2 else '?'} → {last.get('value'):,} mappers")

    return result


def query_contributions() -> dict:
    """Query C: Total edit contributions over time."""
    print("\n[Query C] Edit contributions over time...")
    body = {
        "filter": POI_FILTER,
        "bboxes": SG_BBOX,
        "time": TIME_RANGE,
    }
    result = ohsome_post("/contributions/count", body, "Contributions")

    if "result" in result:
        values = result["result"]
        print(f"    {len(values)} time points returned")
        if values:
            first = values[0]
            last = values[-1]
            print(f"    First: {first.get('fromTimestamp','')[:10]} → {first.get('value')} edits")
            print(f"    Last:  {last.get('fromTimestamp','')[:10]} → {last.get('value')} edits")

    return result


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ohsome Quality Metrics — Singapore POI Data")
    print("=" * 60)

    results = {}

    # Run all 3 queries
    try:
        results["poi_count"] = query_poi_count()
        time.sleep(2)
    except Exception as e:
        print(f"    FAILED: {e}")
        results["poi_count"] = {"error": str(e)}

    try:
        results["user_count"] = query_user_count()
        time.sleep(2)
    except Exception as e:
        print(f"    FAILED: {e}")
        results["user_count"] = {"error": str(e)}

    try:
        results["contributions"] = query_contributions()
        time.sleep(2)
    except Exception as e:
        print(f"    FAILED: {e}")
        results["contributions"] = {"error": str(e)}

    # Save combined results
    out_path = DATA_DIR / "ohsome_quality_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    size_kb = out_path.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"Saved: {out_path} ({size_kb:.1f} KB)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
