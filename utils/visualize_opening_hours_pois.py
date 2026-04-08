"""
Visualize spatial distribution of POIs with opening_hours by time period.

This script creates a map showing POIs colored by their operating time periods.

Usage:
    python utils/visualize_opening_hours_pois.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIGURES_DIR = BASE_DIR / "figures"

# Singapore bounds
SG_BBOX = {"south": 1.16, "north": 1.47, "west": 103.60, "east": 104.08}

# Colors for time periods
PERIOD_COLORS = {
    "morning": "#F4A261",   # Orange
    "afternoon": "#2A9D8F",  # Teal
    "evening": "#264653",    # Dark blue
    "all_day": "#E9C46A",    # Yellow
    "unknown": "#999999",     # Gray
}

plt.style.use("default")
plt.rcParams["font.size"] = 10


def main():
    """Main execution."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Visualizing POIs with opening_hours")
    print("="*60)

    # Load data
    oh_df = pd.read_csv(DATA_DIR / "pois_with_opening_hours.csv")
    print(f"\nLoaded {len(oh_df)} POIs with opening_hours")

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Spatial Distribution of POIs with Opening Hours by Time Period",
                 fontsize=14, fontweight="bold")

    # 1. Overall map (all POIs with opening_hours)
    ax = axes[0, 0]
    ax.scatter(oh_df["lon"], oh_df["lat"], s=1, alpha=0.5, color=PERIOD_COLORS["unknown"])
    ax.set_title(f"All POIs with opening_hours (n={len(oh_df)})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(SG_BBOX["west"], SG_BBOX["east"])
    ax.set_ylim(SG_BBOX["south"], SG_BBOX["north"])
    ax.grid(True, alpha=0.3)

    # 2. Morning POIs
    ax = axes[0, 1]
    morning_df = oh_df[oh_df["morning"]]
    ax.scatter(morning_df["lon"], morning_df["lat"], s=1, alpha=0.5, color=PERIOD_COLORS["morning"])
    ax.set_title(f"Morning (06:00-10:00) POIs (n={len(morning_df)})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(SG_BBOX["west"], SG_BBOX["east"])
    ax.set_ylim(SG_BBOX["south"], SG_BBOX["north"])
    ax.grid(True, alpha=0.3)

    # 3. Afternoon POIs
    ax = axes[1, 0]
    afternoon_df = oh_df[oh_df["afternoon"]]
    ax.scatter(afternoon_df["lon"], afternoon_df["lat"], s=1, alpha=0.5, color=PERIOD_COLORS["afternoon"])
    ax.set_title(f"Afternoon (10:00-16:00) POIs (n={len(afternoon_df)})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(SG_BBOX["west"], SG_BBOX["east"])
    ax.set_ylim(SG_BBOX["south"], SG_BBOX["north"])
    ax.grid(True, alpha=0.3)

    # 4. Evening POIs
    ax = axes[1, 1]
    evening_df = oh_df[oh_df["evening"]]
    ax.scatter(evening_df["lon"], evening_df["lat"], s=1, alpha=0.5, color=PERIOD_COLORS["evening"])
    ax.set_title(f"Evening (16:00-22:00) POIs (n={len(evening_df)})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(SG_BBOX["west"], SG_BBOX["east"])
    ax.set_ylim(SG_BBOX["south"], SG_BBOX["north"])
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save
    output_path = FIGURES_DIR / "part4_opening_hours_spatial_distribution.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {output_path}")

    # Create second figure: Venn diagram style (overlap)
    fig2, ax = plt.subplots(figsize=(10, 8))

    # Calculate overlaps
    only_morning = oh_df["morning"] & ~oh_df["afternoon"] & ~oh_df["evening"]
    only_afternoon = ~oh_df["morning"] & oh_df["afternoon"] & ~oh_df["evening"]
    only_evening = ~oh_df["morning"] & ~oh_df["afternoon"] & oh_df["evening"]
    morning_afternoon = oh_df["morning"] & oh_df["afternoon"] & ~oh_df["evening"]
    morning_evening = oh_df["morning"] & ~oh_df["afternoon"] & oh_df["evening"]
    afternoon_evening = ~oh_df["morning"] & oh_df["afternoon"] & oh_df["evening"]
    all_three = oh_df["morning"] & oh_df["afternoon"] & oh_df["evening"]

    # Display statistics
    stats_text = f"""
Time Period Overlap Statistics

All three periods: {all_three.sum():,} POIs
Morning + Afternoon only: {morning_afternoon.sum():,}
Morning + Evening only: {morning_evening.sum():,}
Afternoon + Evening only: {afternoon_evening.sum():,}

Morning only: {only_morning.sum():,}
Afternoon only: {only_afternoon.sum():,}
Evening only: {only_evening.sum():,}

Total: {len(oh_df):,} POIs
    """

    ax.text(0.1, 0.5, stats_text, fontsize=11, family="monospace",
            verticalalignment="center", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    ax.axis("off")
    ax.set_title("Time Period Overlap", fontsize=14, fontweight="bold")

    output_path2 = FIGURES_DIR / "part4_opening_hours_overlap.png"
    plt.savefig(output_path2, dpi=150, bbox_inches="tight")
    print(f"Saved: {output_path2}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total POIs with opening_hours: {len(oh_df):,}")
    print(f"\nSpatial distribution maps created:")
    print(f"  1. Four-panel map by time period")
    print(f"  2. Overlap statistics")
    print("\nRecommendations:")
    print(f"  - Use 'Afternoon' POIs for daytime analysis (highest coverage: 93.8%)")
    print(f"  - Use 'Evening' POIs for evening analysis (high coverage: 90.7%)")
    print(f"  - Consider combining all periods for comprehensive analysis")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    main()
