"""
Visualize historical POI snapshots and cross-reference with ohsome data.

This script compares POI counts from:
1. Our historical Overpass snapshots
2. ohsome API aggregate statistics

This helps validate data quality and understand urban evolution.

Usage:
    python utils/visualize_historical_pois.py
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import glob

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORICAL_DIR = DATA_DIR / "historical_pois"
FIGURES_DIR = BASE_DIR / "figures"

# Snapshot years to compare
YEARS = [2020, 2022, 2024]

plt.style.use("default")
plt.rcParams["font.size"] = 10


def load_historical_counts() -> pd.DataFrame:
    """Load POI counts from historical snapshots."""
    print("Loading historical snapshot data...")

    counts = []
    for year in YEARS:
        csv_path = HISTORICAL_DIR / f"historical_pois_{year}-01-01.csv"

        if not csv_path.exists():
            print(f"  WARNING: {csv_path} not found")
            continue

        df = pd.read_csv(csv_path)
        # Count unique POI classes (primary category)
        df["poi_class"] = df.apply(lambda row: assign_primary_class(row), axis=1)
        df = df[df["poi_class"] != ""]

        counts.append({
            "year": year,
            "total_pois": len(df),
            "unique_classes": df["poi_class"].nunique()
        })
        print(f"  {year}: {len(df):,} POIs, {df['poi_class'].nunique()} classes")

    return pd.DataFrame(counts)


def assign_primary_class(row):
    """Assign primary POI class (same logic as Part 3)."""
    keys = ["amenity", "shop", "leisure", "tourism", "office", "healthcare", "craft", "historic"]
    for key in keys:
        val = row.get(key)
        if pd.notna(val) and val != "":
            return f"{key}={val}"
    return ""


def load_ohsome_counts() -> pd.DataFrame:
    """Load POI counts from ohsome API results."""
    print("\nLoading ohsome quality data...")

    ohsome_path = DATA_DIR / "ohsome_quality_results.json"
    if not ohsome_path.exists():
        print("  WARNING: ohsome data not found")
        return None

    with open(ohsome_path, "r") as f:
        data = json.load(f)

    # Extract yearly averages from ohsome monthly data
    poi_results = data["poi_count"]["result"]

    yearly_data = []
    for year in YEARS:
        year_results = [r for r in poi_results if r["timestamp"][0:4] == str(year)]
        if year_results:
            avg_count = sum(r["value"] for r in year_results) / len(year_results)
            yearly_data.append({
                "year": year,
                "ohsome_count": avg_count
            })
            print(f"  {year}: {avg_count:,.0f} POIs (ohsome)")

    return pd.DataFrame(yearly_data)


def visualize_comparison(historical_df: pd.DataFrame, ohsome_df: pd.DataFrame):
    """Create comparison visualizations."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1. POI Count Comparison
    ax = axes[0]
    x = np.arange(len(YEARS))
    width = 0.35

    ax.bar(x - width/2, historical_df["total_pois"], width,
           label="Overpass Snapshots", color="#2D6A4F", alpha=0.8)
    ax.bar(x + width/2, ohsome_df["ohsome_count"], width,
           label="ohsome API", color="#E9C46A", alpha=0.8)

    ax.set_xlabel("Year")
    ax.set_ylabel("POI Count")
    ax.set_title("Historical POI Count: Overpass vs ohsome")
    ax.set_xticks(x)
    ax.set_xticklabels(YEARS)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Add value labels
    for i, (overpass, ohsome) in enumerate(zip(historical_df["total_pois"], ohsome_df["ohsome_count"])):
        ax.text(i - width/2, overpass, f"{int(overpass):,}",
                ha="center", va="bottom", fontsize=8)
        ax.text(i + width/2, ohsome, f"{int(ohsome):,}",
                ha="center", va="bottom", fontsize=8)

    # 2. Growth Rate Comparison
    ax = axes[1]

    # Calculate growth rates
    hist_growth = historical_df["total_pois"].pct_change() * 100
    ohsome_growth = ohsome_df["ohsome_count"].pct_change() * 100

    # Align growth rates (ohsome has one more year)
    growth_years = YEARS[1:]  # Exclude first year (no growth)
    x = np.arange(len(growth_years))

    ax.bar(x - width/2, hist_growth.iloc[1:], width,
           label="Overpass Snapshots", color="#2D6A4F", alpha=0.8)
    ax.bar(x + width/2, ohsome_growth.iloc[:-1], width,
           label="ohsome API", color="#E9C46A", alpha=0.8)

    ax.set_xlabel("Year")
    ax.set_ylabel("Growth Rate (%)")
    ax.set_title("Year-over-Year POI Growth Rate")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{y-1}→{y}" for y in growth_years])
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    # Add value labels
    for i, (hg, og) in enumerate(zip(hist_growth.iloc[1:], ohsome_growth.iloc[:-1])):
        ax.text(i - width/2, hg, f"{hg:.1f}%",
                ha="center", va="bottom" if hg >= 0 else "top", fontsize=8)
        ax.text(i + width/2, og, f"{og:.1f}%",
                ha="center", va="bottom" if og >= 0 else "top", fontsize=8)

    plt.tight_layout()

    # Save
    output_path = FIGURES_DIR / "part2_historical_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {output_path}")
    plt.close()

    # Create summary table
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)

    comparison = historical_df.merge(ohsome_df, on="year")
    comparison["difference"] = comparison["total_pois"] - comparison["ohsome_count"]
    comparison["pct_diff"] = comparison["difference"] / comparison["ohsome_count"] * 100

    print("\nYear-by-Year Comparison:")
    print(comparison[["year", "total_pois", "ohsome_count", "difference", "pct_diff"]].to_string(index=False))

    return comparison


def main():
    """Main execution."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Historical POI Snapshot Visualization")
    print("="*60)

    # Check if historical data exists
    historical_files = list(HISTORICAL_DIR.glob("historical_pois_*.csv"))

    if not historical_files:
        print("\nERROR: No historical snapshot data found!")
        print(f"\nExpected files in {HISTORICAL_DIR}/")
        print("Please run: python utils/download_historical_pois.py --years 2020 2022 2024")
        return

    print(f"\nFound {len(historical_files)} historical snapshot files")

    # Load data
    historical_df = load_historical_counts()
    ohsome_df = load_ohsome_counts()

    if ohsome_df is None:
        print("\nERROR: ohsome data not available for comparison")
        return

    # Visualize
    visualize_comparison(historical_df, ohsome_df)

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Analyze the comparison - are counts consistent?")
    print("2. If consistent → reliable historical snapshots")
    print("3. Run LDA on each historical snapshot")
    print("4. Compare topic evolution over time")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    main()
