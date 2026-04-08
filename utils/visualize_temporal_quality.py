"""
Visualize temporal OSM data quality metrics from ohsome API results.

This script creates three time-series plots showing:
1. POI count growth over time (2020-2026)
2. Active mapper count over time
3. Total edit contributions over time

These visualizations help understand data quality trends and identify periods
of high mapping activity that may affect snapshot comparisons in Part 2.

Usage:
    python utils/visualize_temporal_quality.py
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime

# === Config ===
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIGURES_DIR = BASE_DIR / "figures"

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


def load_ohsome_data() -> dict:
    """Load ohsome quality results from JSON."""
    ohsome_path = DATA_DIR / "ohsome_quality_results.json"

    if not ohsome_path.exists():
        raise FileNotFoundError(
            f"ohsome data not found: {ohsome_path}\n"
            "Please run utils/ohsome_quality.py first to query the ohsome API."
        )

    print(f"Loading ohsome data from {ohsome_path}...")
    with open(ohsome_path, "r") as f:
        data = json.load(f)

    print(f"  Found {len(data)} metrics: {list(data.keys())}")
    return data


def parse_ohsome_result(result_data: list, time_field: str = "timestamp") -> pd.DataFrame:
    """Parse ohsome API result into a pandas DataFrame."""
    records = []
    for item in result_data:
        if time_field == "timestamp":
            time_str = item.get("timestamp", "")
        else:  # fromTimestamp for contributions/user_count
            time_str = item.get("fromTimestamp", "")

        # Parse timestamp
        if time_str:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        else:
            dt = None

        records.append({
            "date": dt,
            "value": item.get("value", 0)
        })

    df = pd.DataFrame(records)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def aggregate_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly data to yearly averages."""
    df = df.copy()
    df["year"] = df["date"].dt.year
    yearly = df.groupby("year").agg({
        "value": ["mean", "first", "last"]
    }).reset_index()
    yearly.columns = ["year", "mean", "first", "last"]
    yearly["growth"] = (yearly["last"] - yearly["first"]) / yearly["first"] * 100
    return yearly


def plot_poi_count_timeseries(poi_df: pd.DataFrame) -> plt.Figure:
    """Create time series plot of POI count over time."""
    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot line
    ax.plot(
        poi_df["date"], poi_df["value"],
        color=PROJECT_COLORS["mrt_green"],
        linewidth=2,
        marker="o",
        markersize=3,
        alpha=0.7
    )

    # Add trend line annotation
    first_val = poi_df["value"].iloc[0]
    last_val = poi_df["value"].iloc[-1]
    growth_pct = (last_val - first_val) / first_val * 100

    # Annotate start and end points
    ax.annotate(
        f"{first_val:,.0f}",
        xy=(poi_df["date"].iloc[0], first_val),
        xytext=(10, 10), textcoords="offset points",
        fontsize=9, color=PROJECT_COLORS["mrt_green"],
        fontweight="bold"
    )
    ax.annotate(
        f"{last_val:,.0f}",
        xy=(poi_df["date"].iloc[-1], last_val),
        xytext=(-10, 10), textcoords="offset points",
        fontsize=9, color=PROJECT_COLORS["mrt_green"],
        fontweight="bold", ha="right"
    )

    # Formatting
    ax.set_title(
        f"Singapore POI Count Over Time (Growth: +{growth_pct:.1f}%)",
        fontsize=12, fontweight="bold"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Total POI Count")
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45, ha="right")

    # Add reference lines for key periods
    ax.axvline(
        pd.Timestamp("2022-01-01"), color="gray",
        linestyle="--", alpha=0.5, linewidth=1
    )
    ax.text(
        pd.Timestamp("2022-01-01"), ax.get_ylim()[1] * 0.95,
        "2022", fontsize=8, color="gray", ha="center"
    )

    plt.tight_layout()
    return fig


def plot_mapper_activity_timeseries(user_df: pd.DataFrame) -> plt.Figure:
    """Create time series plot of unique mapper count over time."""
    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot line
    ax.plot(
        user_df["date"], user_df["value"],
        color=PROJECT_COLORS["ntu_orange"],
        linewidth=2,
        marker="o",
        markersize=3,
        alpha=0.7
    )

    # Add statistics
    mean_val = user_df["value"].mean()
    max_val = user_df["value"].max()
    min_val = user_df["value"].min()

    # Add horizontal line for mean
    ax.axhline(
        mean_val, color=PROJECT_COLORS["ntu_orange"],
        linestyle="--", alpha=0.5, linewidth=1
    )
    ax.text(
        ax.get_xlim()[1], mean_val,
        f"Mean: {mean_val:.0f}",
        fontsize=8, color=PROJECT_COLORS["ntu_orange"],
        va="bottom", ha="right"
    )

    # Annotate peak
    peak_idx = user_df["value"].idxmax()
    ax.annotate(
        f"Peak: {max_val}",
        xy=(user_df["date"].iloc[peak_idx], max_val),
        xytext=(0, 10), textcoords="offset points",
        fontsize=8, color=PROJECT_COLORS["ntu_orange"],
        ha="center", fontweight="bold"
    )

    # Formatting
    ax.set_title(
        f"Active OSM Mappers Over Time (Mean: {mean_val:.0f}, Range: {min_val:.0f}-{max_val:.0f})",
        fontsize=12, fontweight="bold"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Unique Mappers (per month)")
    ax.grid(True, alpha=0.3)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    return fig


def plot_contributions_timeseries(contrib_df: pd.DataFrame) -> plt.Figure:
    """Create time series plot of edit contributions over time."""
    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot line
    ax.plot(
        contrib_df["date"], contrib_df["value"],
        color=PROJECT_COLORS["bus_red"],
        linewidth=2,
        marker="o",
        markersize=3,
        alpha=0.7
    )

    # Add statistics
    mean_val = contrib_df["value"].mean()
    median_val = contrib_df["value"].median()
    max_val = contrib_df["value"].max()

    # Add horizontal lines
    ax.axhline(
        mean_val, color=PROJECT_COLORS["bus_red"],
        linestyle="--", alpha=0.5, linewidth=1, label=f"Mean: {mean_val:.0f}"
    )
    ax.axhline(
        median_val, color=PROJECT_COLORS["bus_red"],
        linestyle=":", alpha=0.5, linewidth=1, label=f"Median: {median_val:.0f}"
    )

    # Highlight spikes (high activity periods)
    threshold = mean_val + 2 * contrib_df["value"].std()
    spikes = contrib_df[contrib_df["value"] > threshold]

    for _, spike in spikes.iterrows():
        ax.scatter(
            spike["date"], spike["value"],
            color="red", s=50, zorder=5, alpha=0.7
        )

    if len(spikes) > 0:
        ax.text(
            ax.get_xlim()[1], ax.get_ylim()[1] * 0.9,
            f"High activity periods: {len(spikes)} months",
            fontsize=8, color="red", ha="right",
            bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.3)
        )

    # Formatting
    ax.set_title(
        f"Monthly Edit Contributions (Mean: {mean_val:.0f}, Max: {max_val:.0f})",
        fontsize=12, fontweight="bold"
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Edits (per month)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    return fig


def plot_poi_yearly_changes(poi_df: pd.DataFrame) -> plt.Figure:
    """Create bar chart showing POI count changes by year."""
    # Aggregate by year
    yearly = aggregate_by_year(poi_df)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Create bar positions
    x_pos = np.arange(len(yearly))
    bars = ax.bar(
        x_pos,
        yearly["last"],
        color=[PROJECT_COLORS["mrt_green"] if g > 0 else PROJECT_COLORS["bus_red"]
               for g in yearly["growth"]],
        alpha=0.7,
        edgecolor="white",
        linewidth=1.5
    )

    # Add value labels on bars
    for i, (bar, val, growth) in enumerate(zip(bars, yearly["last"], yearly["growth"])):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2., height,
            f"{val:,.0f}\n(+{growth:.1f}%)",
            ha="center", va="bottom",
            fontsize=8,
            fontweight="bold"
        )

    # Add line connecting bars to show trend
    ax.plot(
        x_pos,
        yearly["last"],
        color=PROJECT_COLORS["nus_blue"],
        linewidth=2,
        marker="o",
        markersize=8,
        alpha=0.8,
        label="Trend line"
    )

    # Formatting
    ax.set_title(
        "Annual POI Count Growth (2020-2026)",
        fontsize=14, fontweight="bold"
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("POI Count (end of year)")
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{int(y)}" for y in yearly["year"]])
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(loc="upper left")

    # Add summary text
    total_growth = (yearly["last"].iloc[-1] - yearly["first"].iloc[0]) / yearly["first"].iloc[0] * 100
    ax.text(
        0.02, 0.98,
        f"Total Growth: +{total_growth:.1f}%\n"
        f"{int(yearly['first'].iloc[0]):,} → {int(yearly['last'].iloc[-1]):,} POIs",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    )

    plt.tight_layout()
    return fig


def create_summary_stats(data: dict) -> dict:
    """Calculate summary statistics from ohsome data."""
    poi_df = parse_ohsome_result(data["poi_count"]["result"])
    user_df = parse_ohsome_result(
        data["user_count"]["result"],
        time_field="fromTimestamp"
    )
    contrib_df = parse_ohsome_result(
        data["contributions"]["result"],
        time_field="fromTimestamp"
    )

    stats = {
        "poi_count": {
            "first_value": int(poi_df["value"].iloc[0]),
            "last_value": int(poi_df["value"].iloc[-1]),
            "growth_pct": round(
                (poi_df["value"].iloc[-1] - poi_df["value"].iloc[0]) /
                poi_df["value"].iloc[0] * 100, 2
            ),
            "first_date": poi_df["date"].iloc[0].strftime("%Y-%m-%d"),
            "last_date": poi_df["date"].iloc[-1].strftime("%Y-%m-%d"),
        },
        "mapper_activity": {
            "mean": round(user_df["value"].mean(), 1),
            "max": int(user_df["value"].max()),
            "min": int(user_df["value"].min()),
            "std": round(user_df["value"].std(), 1),
        },
        "contributions": {
            "mean": round(contrib_df["value"].mean(), 1),
            "median": round(contrib_df["value"].median(), 1),
            "max": int(contrib_df["value"].max()),
            "total": int(contrib_df["value"].sum()),
        }
    }

    return stats


def main():
    """Main execution."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Temporal OSM Data Quality Visualization")
    print("="*60)

    # Load data
    data = load_ohsome_data()

    # Parse dataframes
    print("\nParsing time series data...")
    poi_df = parse_ohsome_result(data["poi_count"]["result"])
    user_df = parse_ohsome_result(
        data["user_count"]["result"],
        time_field="fromTimestamp"
    )
    contrib_df = parse_ohsome_result(
        data["contributions"]["result"],
        time_field="fromTimestamp"
    )

    print(f"  POI count: {len(poi_df)} time points")
    print(f"  User count: {len(user_df)} time points")
    print(f"  Contributions: {len(contrib_df)} time points")

    # Create visualizations
    print("\nCreating visualizations...")

    # 1. POI count time series
    fig1 = plot_poi_count_timeseries(poi_df)
    output1 = FIGURES_DIR / "part3_poi_count_timeseries.png"
    fig1.savefig(output1, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output1}")
    plt.close(fig1)

    # 2. Mapper activity time series
    fig2 = plot_mapper_activity_timeseries(user_df)
    output2 = FIGURES_DIR / "part3_mapper_activity_timeseries.png"
    fig2.savefig(output2, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output2}")
    plt.close(fig2)

    # 3. Contributions time series
    fig3 = plot_contributions_timeseries(contrib_df)
    output3 = FIGURES_DIR / "part3_contributions_timeseries.png"
    fig3.savefig(output3, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output3}")
    plt.close(fig3)

    # 4. Yearly POI changes
    fig4 = plot_poi_yearly_changes(poi_df)
    output4 = FIGURES_DIR / "part3_poi_yearly_changes.png"
    fig4.savefig(output4, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output4}")
    plt.close(fig4)

    # Calculate and save summary statistics
    stats = create_summary_stats(data)
    stats_path = DATA_DIR / "temporal_quality_summary.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nSaved summary to {stats_path}")

    # Print summary
    print("\n" + "="*60)
    print("TEMPORAL QUALITY SUMMARY")
    print("="*60)
    print(f"\nPOI Count:")
    print(f"  {stats['poi_count']['first_date']}: {stats['poi_count']['first_value']:,}")
    print(f"  {stats['poi_count']['last_date']}: {stats['poi_count']['last_value']:,}")
    print(f"  Growth: +{stats['poi_count']['growth_pct']}%")

    print(f"\nMapper Activity:")
    print(f"  Mean: {stats['mapper_activity']['mean']} mappers/month")
    print(f"  Range: {stats['mapper_activity']['min']} - {stats['mapper_activity']['max']}")
    print(f"  Std Dev: {stats['mapper_activity']['std']}")

    print(f"\nEdit Contributions:")
    print(f"  Mean: {stats['contributions']['mean']} edits/month")
    print(f"  Median: {stats['contributions']['median']}")
    print(f"  Peak: {stats['contributions']['max']} (highest month)")
    print(f"  Total: {stats['contributions']['total']:,} edits (2020-2026)")

    print("\n" + "="*60)
    print("DONE")
    print("="*60)


if __name__ == "__main__":
    main()
