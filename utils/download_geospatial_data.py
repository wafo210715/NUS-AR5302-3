"""
Download geospatial data for NUS/NTU station identification.

Uses small bounding boxes around each campus to query OSM (Overpass API).
This avoids timeouts from querying all of Singapore at once.

Outputs (saved to data/):
  - nus_boundary.geojson
  - ntu_boundary.geojson
  - sg_bus_stops.csv
  - sg_mrt_stations.csv
"""

import csv
import json
import time
import urllib.request
from pathlib import Path

# === Config ===
DATA_DIR = Path("data")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MAX_RETRIES = 3
RETRY_DELAY = 15

DATA_DIR.mkdir(exist_ok=True)

# Small bounding boxes around each campus (~3km x 3km)
BBOXES = {
    "NUS": (1.285, 103.765, 1.315, 103.795),
    "NTU": (1.335, 103.670, 1.365, 103.710),
}

# Known MRT station code mappings
CODE_MAP = {
    "Kent Ridge": "CC24",
    "Boon Lay": "EW27",
    "Pioneer": "EW28",
}


def overpass_query(query: str, label: str) -> dict:
    """Query Overpass API with retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            payload = f"[out:json][timeout:60];{query}".encode("utf-8")
            req = urllib.request.Request(
                OVERPASS_URL,
                data=payload,
                headers={"User-Agent": "NUS-AR5302-Project/1.0"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [{label}] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def download_bus_stops() -> None:
    """Download bus stops near NUS and NTU from OSM."""
    print("Downloading bus stops near campuses from OSM...")
    rows = []

    for campus, (s, w, n, e) in BBOXES.items():
        print(f"  Querying {campus} area ({s},{w},{n},{e})...")

        query = f'node["highway"="bus_stop"]({s},{w},{n},{e});out;'

        result = overpass_query(query, f"{campus} bus stops")

        for el in result.get("elements", []):
            tags = el.get("tags", {})
            rows.append({
                "osm_id": el.get("id"),
                "name": tags.get("name", ""),
                "latitude": el.get("lat"),
                "longitude": el.get("lon"),
                "campus": campus,
            })

        print(f"    Found {len(result.get('elements', []))} bus stops")
        time.sleep(3)

    out_path = DATA_DIR / "sg_bus_stops.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved {len(rows)} total bus stops to {out_path}")


def download_campus_boundary(name: str, filename: str) -> None:
    """Download a university campus boundary polygon from OSM."""
    print(f"Downloading {name} boundary from OSM...")

    query = f"""
    (
      relation["amenity"="university"]["name"="{name}"];
    );
    out geom;
    """

    result = overpass_query(query, name)

    elements = result.get("elements", [])
    if not elements:
        raise ValueError(f"No OSM relation found for '{name}'")

    element = elements[0]
    members = element.get("members", [])

    coords = []
    for member in members:
        if member.get("type") == "way" and member.get("role") == "outer":
            geometry = member.get("geometry", [])
            for point in geometry:
                coords.append([point["lon"], point["lat"]])

    if not coords:
        raise ValueError(f"No coordinates found for '{name}' boundary")

    if coords[0] != coords[-1]:
        coords.append(coords[0])

    geojson = {
        "type": "Feature",
        "properties": {
            "name": name,
            "osm_id": element.get("id"),
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords],
        },
    }

    out_path = DATA_DIR / filename
    with open(out_path, "w") as f:
        json.dump(geojson, f, indent=2)

    print(f"  Saved {name} boundary ({len(coords)} points) to {out_path}")


def download_mrt_stations() -> None:
    """Download MRT stations near campuses from OSM."""
    print("Downloading MRT stations near campuses from OSM...")
    rows = []

    for campus, (s, w, n, e) in BBOXES.items():
        print(f"  Querying {campus} area...")

        query = f"""
        (
          node["railway"="station"]({s},{w},{n},{e});
          node["station"="light_rail"]({s},{w},{n},{e});
        );
        out;
        """

        result = overpass_query(query, f"{campus} MRT")

        for el in result.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name", "")
            station_code = ""
            for pattern, code in CODE_MAP.items():
                if pattern.lower() in name.lower():
                    station_code = code
                    break
            rows.append({
                "osm_id": el.get("id"),
                "station_code": station_code,
                "station_name": name,
                "latitude": el.get("lat"),
                "longitude": el.get("lon"),
                "campus": campus,
            })

        print(f"    Found {len(result.get('elements', []))} stations")
        time.sleep(3)

    out_path = DATA_DIR / "sg_mrt_stations.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved {len(rows)} total MRT stations to {out_path}")


if __name__ == "__main__":
    print("=" * 50)
    print("Geospatial Data Download (OSM / Overpass)")
    print("=" * 50)

    download_bus_stops()
    time.sleep(3)

    download_campus_boundary(
        "National University of Singapore",
        "nus_boundary.geojson",
    )
    time.sleep(3)

    download_campus_boundary(
        "Nanyang Technological University",
        "ntu_boundary.geojson",
    )
    time.sleep(3)

    download_mrt_stations()

    print("\n" + "=" * 50)
    print("All downloads complete. Files in data/:")
    for f in ["sg_bus_stops.csv", "sg_mrt_stations.csv",
              "nus_boundary.geojson", "ntu_boundary.geojson"]:
        path = DATA_DIR / f
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"  {f} ({size:.1f} KB)")
        else:
            print(f"  {f} — MISSING")
    print("=" * 50)
