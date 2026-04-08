"""
Visualize POI coverage across Singapore's 4 sub-regions to validate complete data collection.

This script creates a heatmap visualization showing POI density in each of the 4 sub-regions
used for Overpass API queries. This helps verify that all regions were successfully crawled
and identifies any potential API timeouts or data gaps.

Usage:
    python utils/visualize_poi_coverage.py
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
import numpy as np

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIGURES_DIR = BASE_DIR / "figures"

# Singapore bounding box
SG_BBOX = (1.16, 103.60, 1.47, 104.08)

# 4 sub-regions from download_pois.py
SUB_REGIONS = {
    "Northwest": (1.16, 103.60, 1.32, 103.84),
    "Northeast": (1.32, 103.60, 1.47, 103.84),
    "Southwest": (1.16, 103.84, 1.32, 104.08),
    "Southeast": (1.32, 103.84, 1.47, 104.08),
}

# Project colors (matching R's project_colors)
PROJECT_COLORS = {
    "nus_blue": "#003D7C",
    "ntu_orange": "#E85D04",
    "bus_red": "#D62828",
    "mrt_green": "#2D6A4F",
}

# Set matplotlib style
plt.style.use("default")
plt.rcParams["font.size"] = 10
plt.rcParams["figure.dpi"] = 150


def load_pois() -> pd.DataFrame:
    """Load POI data from CSV."""
    poi_path = DATA_DIR / "sg_pois_all.csv"

    if not poi_path.exists():
        raise FileNotFoundError(
            f"POI data not found: {poi_path}\n"
            "Please run utils/download_pois.py first to download POI data."
        )

    print(f"\nLoading POI data from {poi_path}...")
    df = pd.read_csv(poi_path)
    print(f"  Loaded {len(df)} POIs")

    return df


def count_pois_by_region(pois: pd.DataFrame) -> dict:
    """Count POIs in each sub-region."""
    region_counts = {}

    for region_name, (s, w, n, e) in SUB_REGIONS.items():
        # Filter POIs within this region's bounding box
        mask = (
            (pois["lat"] >= s) & (pois["lat"] < n) &
            (pois["lon"] >= w) & (pois["lon"] < e)
        )
        count = mask.sum()
        region_counts[region_name] = count
        print(f"  {region_name}: {count:,} POIs")

    return region_counts


def create_coverage_map(pois: pd.DataFrame, region_counts: dict) -> plt.Figure:
    """Create a 2x2 subplot grid showing POI density in each sub-region."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(
        "POI Coverage Validation: Singapore 4 Sub-Regions",
        fontsize=14, fontweight="bold", y=0.98
    )

    # Position labels for the 2x2 grid
    positions = [
        (0, 1, "Northwest"), (0, 0, "Northeast"),
        (1, 1, "Southwest"), (1, 0, "Southeast"),
    ]

    total_pois = len(pois)

    for row, col, region_name in positions:
        ax = axes[row, col]
        s, w, n, e = SUB_REGIONS[region_name]
        count = region_counts[region_name]

        # Filter POIs for this region
        mask = (
            (pois["lat"] >= s) & (pois["lat"] < n) &
            (pois["lon"] >= w) & (pois["lon"] < e)
        )
        region_pois = pois[mask]

        # Create 2D histogram (heatmap)
        if len(region_pois) > 0:
            nbins = 50
            hist, xedges, yedges = np.histogram2d(
                region_pois["lon"], region_pois["lat"],
                bins=nbins, range=[[w, e], [s, n]]
            )

            # Plot heatmap
            im = ax.imshow(
                hist.T, origin="lower", extent=[w, e, s, n],
                cmap="YlOrRd", aspect="auto", interpolation="nearest"
            )
            plt.colorbar(im, ax=ax, label="POI Count", shrink=0.8)

        # Set plot properties
        ax.set_title(f"{region_name}: {count:,} POIs ({count/total_pois*100:.1f}%)", fontweight="bold")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_xlim(w, e)
        ax.set_ylim(s, n)
        ax.grid(True, alpha=0.3)

        # Add annotation if count is low (potential API timeout)
        if count < 5000:
            ax.text(
                0.5, 0.5, f"WARNING: Low POI count!\nPossible API timeout",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=10, color="red", fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.7)
            )

    plt.tight_layout()
    return fig


def create_overview_map(pois: pd.DataFrame, region_counts: dict) -> plt.Figure:
    """Create an overview map showing all 4 regions with their boundaries."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot all POIs as small dots
    ax.scatter(
        pois["lon"], pois["lat"],
        s=0.5, alpha=0.3, color=PROJECT_COLORS["bus_red"]
    )

    # Draw region boundaries
    colors = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A"]

    for (region_name, (s, w, n, e)), color in zip(SUB_REGIONS.items(), colors):
        # Draw rectangle
        width = e - w
        height = n - s
        rect = patches.Rectangle(
            (w, s), width, height,
            linewidth=2, edgecolor=color, facecolor="none", alpha=0.8
        )
        ax.add_patch(rect)

        # Add label
        center_x = w + width / 2
        center_y = s + height / 2
        count = region_counts[region_name]

        ax.text(
            center_x, center_y,
            f"{region_name}\n{count:,} POIs",
            ha="center", va="center",
            fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8)
        )

    ax.set_title("Singapore POI Coverage Overview", fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(SG_BBOX[1], SG_BBOX[3])
    ax.set_ylim(SG_BBOX[0], SG_BBOX[2])
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def save_summary(region_counts: dict, total_pois: int):
    """Save summary statistics to JSON."""
    summary = {
        "total_pois": int(total_pois),
        "expected_range": [100000, 200000],
        "is_below_expectation": total_pois < 100000,
        "regions": {}
    }

    for name, (s, w, n, e) in SUB_REGIONS.items():
        count = region_counts[name]
        summary["regions"][name] = {
            "count": int(count),
            "percentage": round(count / total_pois * 100, 2),
            "bbox": {"south": float(s), "west": float(w), "north": float(n), "east": float(e)}
        }

    output_path = DATA_DIR / "poi_coverage_summary.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved summary to {output_path}")

    # Print warnings
    print("\n" + "="*60)
    print("COVERAGE VALIDATION RESULTS")
    print("="*60)
    print(f"Total POIs: {total_pois:,}")
    print(f"Expected: 100,000 - 200,000")

    if total_pois < 100000:
        print("\n⚠️  WARNING: POI count is below expectation!")
        print("   Possible causes:")
        print("   - Overpass API timeout in some sub-regions")
        print("   - Overlap between sub-regions causing deduplication")
        print("   - OSM data sparsity in some areas")

    print("\nRegion breakdown:")
    for name, count in region_counts.items():
        pct = count / total_pois * 100
        status = "✓" if count >= 5000 else "⚠️  LOW"
        print(f"  {status} {name:12s}: {count:6,} POIs ({pct:5.1f}%)")


def main():
    """Main execution."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("POI Coverage Validation")
    print("="*60)

    # Load data
    pois = load_pois()

    # Count by region
    print("\nCounting POIs by sub-region...")
    region_counts = count_pois_by_region(pois)

    # Create visualizations
    print("\nCreating visualizations...")

    # 2x2 grid heatmap
    fig1 = create_coverage_map(pois, region_counts)
    output_path1 = FIGURES_DIR / "part3_poi_coverage_validation.png"
    fig1.savefig(output_path1, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_path1}")
    plt.close(fig1)

    # Overview map
    fig2 = create_overview_map(pois, region_counts)
    output_path2 = FIGURES_DIR / "part3_poi_coverage_overview.png"
    fig2.savefig(output_path2, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_path2}")
    plt.close(fig2)

    # Save summary
    save_summary(region_counts, len(pois))

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    main()
