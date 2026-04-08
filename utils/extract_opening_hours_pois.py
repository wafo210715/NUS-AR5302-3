"""
Extract POIs with opening_hours and visualize their geographic distribution.

This script:
1. Extracts POIs that have opening_hours tags
2. Classifies them into time periods (morning, afternoon, evening)
3. Visualizes their spatial distribution

Usage:
    python utils/extract_opening_hours_pois.py
"""

import pandas as pd
import json
from pathlib import Path
import re

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIGURES_DIR = BASE_DIR / "figures"

# Time periods (matching OD data classification)
TIME_PERIODS = {
    "morning": (6, 10),    # 06:00-10:00
    "afternoon": (10, 16),  # 10:00-16:00
    "evening": (16, 22),    # 16:00-22:00
}


def parse_opening_hours(oh_string: str) -> dict:
    """
    Parse OSM opening_hours string and classify into time periods.

    Returns dict with keys: morning, afternoon, evening, night, all_day
    """
    result = {
        "morning": False,
        "afternoon": False,
        "evening": False,
        "night": False,
        "all_day": False,
        "raw": oh_string
    }

    if not oh_string or pd.isna(oh_string):
        return result

    oh = oh_string.lower()

    # Check for 24/7
    if "24/7" in oh or "00:00-24:00" in oh:
        result["all_day"] = True
        result["morning"] = True
        result["afternoon"] = True
        result["evening"] = True
        return result

    # Simple heuristic: check for time ranges
    # This is a simplified parser - full OSM opening_hours parsing is complex

    # Extract all time ranges (e.g., "10:00-22:00", "Mo-Fr 09:00-18:00")
    time_pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})'
    matches = re.findall(time_pattern, oh)

    for match in matches:
        start_hour, _, end_hour, _ = map(int, match)
        start_hour = max(0, min(23, start_hour))
        end_hour = max(0, min(24, end_hour))

        # Check overlap with each period
        if start_hour < TIME_PERIODS["morning"][1] and end_hour > TIME_PERIODS["morning"][0]:
            result["morning"] = True
        if start_hour < TIME_PERIODS["afternoon"][1] and end_hour > TIME_PERIODS["afternoon"][0]:
            result["afternoon"] = True
        if start_hour < TIME_PERIODS["evening"][1] and end_hour > TIME_PERIODS["evening"][0]:
            result["evening"] = True

    # If no specific times found, mark as unknown
    if not any([result["morning"], result["afternoon"], result["evening"]]):
        result["unknown"] = True

    return result


def main():
    """Main execution."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Extracting POIs with opening_hours")
    print("="*60)

    # Load POI data
    poi_path = DATA_DIR / "sg_pois_all.csv"
    print(f"\nLoading POI data from {poi_path}...")
    df = pd.read_csv(poi_path)
    print(f"  Total POIs: {len(df)}")

    # Extract opening_hours from all_tags
    print("\nExtracting opening_hours...")

    opening_hours_data = []
    for idx, row in df.iterrows():
        try:
            tags = json.loads(row["all_tags"].replace('""', '"'))
            if "opening_hours" in tags:
                oh_parsed = parse_opening_hours(tags["opening_hours"])

                # Get primary POI class
                poi_class = None
                for key in ["amenity", "shop", "leisure", "tourism", "office", "healthcare", "craft", "historic"]:
                    val = row.get(key)
                    if pd.notna(val) and val != "":
                        poi_class = f"{key}={val}"
                        break

                opening_hours_data.append({
                    "osm_id": row["osm_id"],
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "poi_class": poi_class,
                    "name": row["name"] if pd.notna(row["name"]) else "",
                    "opening_hours_raw": tags["opening_hours"],
                    **oh_parsed
                })
        except:
            pass

    oh_df = pd.DataFrame(opening_hours_data)
    print(f"  POIs with opening_hours: {len(oh_df)} ({len(oh_df)/len(df)*100:.1f}%)")

    # Time period statistics
    print("\n=== Time Period Coverage ===")
    for period in ["morning", "afternoon", "evening"]:
        count = int(oh_df[period].sum())
        print(f"  {period.capitalize():12s}: {count:4d} POIs ({count/len(oh_df)*100:.1f}%)")

    # POI class breakdown by time period
    print("\n=== Top POI Classes by Time Period ===")
    for period in ["morning", "afternoon", "evening"]:
        period_df = oh_df[oh_df[period]]
        class_counts = period_df["poi_class"].value_counts().head(10)
        print(f"\n{period.capitalize()}:")
        for cls, count in class_counts.items():
            print(f"  {cls}: {count}")

    # Save extracted data
    output_path = DATA_DIR / "pois_with_opening_hours.csv"
    oh_df.to_csv(output_path, index=False)
    print(f"\nSaved to {output_path}")

    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total POIs with opening_hours: {len(oh_df)}")
    print(f"Coverage: {len(oh_df)/len(df)*100:.1f}% of all POIs")

    # Check for POIs that span all three periods
    all_day = oh_df[oh_df["morning"] & oh_df["afternoon"] & oh_df["evening"]]
    print(f"Open all day: {len(all_day)} ({len(all_day)/len(oh_df)*100:.1f}%)")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Create spatial visualization: map POIs by time period")
    print("2. Load OD data and extract time periods")
    print("3. Align time periods between opening_hours and OD data")
    print("4. Run Part 4 analysis on time-period-specific POI sets")

    return oh_df


if __name__ == "__main__":
    main()
