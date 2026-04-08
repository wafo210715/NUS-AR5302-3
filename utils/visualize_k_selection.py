"""
Visualize K selection for LDA: Coherence (C_v) and Perplexity comparison.

Shows how different metrics identify the optimal number of topics.

Usage:
    python utils/visualize_k_selection.py
"""

import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIGURES_DIR = BASE_DIR / "figures"

# Style
plt.style.use("default")
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.facecolor": "white",
})


def load_scores():
    """Load coherence and perplexity scores."""
    with open(DATA_DIR / "coherence_scores_gensim.json") as f:
        gensim_data = json.load(f)

    with open(DATA_DIR / "coherence_scores.json") as f:
        approx_data = json.load(f)

    ks = []
    cv = []
    umass = []
    perplexity_proxy = []

    for key in sorted(gensim_data.keys()):
        d = gensim_data[key]
        ks.append(d["k"])
        cv.append(d["coherence_cv"])
        umass.append(d["coherence_umass"])

    for key in sorted(approx_data.keys()):
        perplexity_proxy.append(approx_data[key]["perplexity_proxy"])

    return ks, cv, umass, perplexity_proxy


def plot_k_selection(ks, cv, umass, perplexity_proxy):
    """Create K selection visualization."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    best_k = ks[np.argmax(cv)]
    best_cv = max(cv)

    # --- Panel 1: C_v Coherence ---
    ax = axes[0]
    ax.plot(ks, cv, "o-", color="#2D6A4F", linewidth=2, markersize=8, zorder=3)
    ax.axvline(x=best_k, color="#E63946", linestyle="--", linewidth=1.5, alpha=0.7,
               label=f"Peak K={best_k}")

    # Highlight the best K
    ax.scatter([best_k], [best_cv], s=150, color="#E63946", zorder=5, edgecolors="black", linewidths=1.5)

    # Annotate each point
    for k, v in zip(ks, cv):
        offset_y = 0.005 if k != best_k else 0.01
        ax.annotate(f"{v:.4f}", (k, v), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=9,
                    fontweight="bold" if k == best_k else "normal",
                    color="#E63946" if k == best_k else "#333333")

    ax.set_xlabel("Number of Topics (K)")
    ax.set_ylabel("C_v Coherence Score")
    ax.set_title("(a) Topic Coherence (C_v)\nHigher = more interpretable")
    ax.set_xticks(ks)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(min(cv) - 0.02, max(cv) + 0.03)

    # --- Panel 2: U_MASS Coherence ---
    ax = axes[1]
    best_k_umass = ks[np.argmax(umass)]
    best_umass = max(umass)

    ax.plot(ks, umass, "s-", color="#457B9D", linewidth=2, markersize=8, zorder=3)
    ax.axvline(x=best_k_umass, color="#E63946", linestyle="--", linewidth=1.5, alpha=0.7,
               label=f"Peak K={best_k_umass}")

    ax.scatter([best_k_umass], [best_umass], s=150, color="#E63946", zorder=5, edgecolors="black", linewidths=1.5)

    for k, v in zip(ks, umass):
        offset = 0.015 if k != best_k_umass else 0.025
        ax.annotate(f"{v:.4f}", (k, v), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=9,
                    fontweight="bold" if k == best_k_umass else "normal",
                    color="#E63946" if k == best_k_umass else "#333333")

    ax.set_xlabel("Number of Topics (K)")
    ax.set_ylabel("U_MASS Coherence Score")
    ax.set_title("(b) Topic Coherence (U_MASS)\nHigher = more interpretable")
    ax.set_xticks(ks)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)

    # --- Panel 3: Perplexity Proxy ---
    ax = axes[2]
    best_k_perp = ks[np.argmin(perplexity_proxy)]
    best_perp = min(perplexity_proxy)

    ax.plot(ks, perplexity_proxy, "D-", color="#E76F51", linewidth=2, markersize=8, zorder=3)

    # Mark elbow (not necessarily lowest)
    ax.scatter([best_k_perp], [best_perp], s=150, color="#E63946", zorder=5, edgecolors="black", linewidths=1.5)

    for k, v in zip(ks, perplexity_proxy):
        ax.annotate(f"{v:.1f}", (k, v), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=9,
                    fontweight="bold" if k == best_k_perp else "normal",
                    color="#E63946" if k == best_k_perp else "#333333")

    ax.set_xlabel("Number of Topics (K)")
    ax.set_ylabel("Perplexity (proxy)")
    ax.set_title("(c) Perplexity\nLower = better model fit")
    ax.set_xticks(ks)
    ax.grid(True, alpha=0.3)
    ax.annotate("No clear elbow\nkeeps decreasing",
                 xy=(ks[-1], perplexity_proxy[-1]),
                 xytext=(ks[-1] - 1.5, perplexity_proxy[0] * 0.95),
                 fontsize=9, fontstyle="italic", color="#666666",
                 arrowprops=dict(arrowstyle="->", color="#999999"))

    plt.tight_layout()

    output = FIGURES_DIR / "part3_k_selection_metrics.png"
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200, bbox_inches="tight")
    print(f"Saved: {output}")
    plt.close()

    # --- Summary ---
    print("\n" + "=" * 55)
    print("K SELECTION SUMMARY")
    print("=" * 55)
    print(f"\n  C_v Coherence:   Peak at K={best_k} ({best_cv:.4f})")
    print(f"  U_MASS Coherence: Peak at K={best_k_umass} ({best_umass:.4f})")
    print(f"  Perplexity:       Lowest at K={best_k_perp} ({best_perp:.1f})")
    print(f"\n  Decision: K={best_k}")
    print(f"  Reason: C_v peak + domain interpretability")
    print(f"  Reference: Lin et al. (2025) used K=6 for London;")
    print(f"             Singapore is more compact, K=5 is justified")

    return output


def plot_cv_detail(ks, cv):
    """Create a standalone detailed C_v plot for the paper."""
    best_k = ks[np.argmax(cv)]
    best_cv = max(cv)

    fig, ax = plt.subplots(figsize=(7, 5))

    # Plot line
    ax.plot(ks, cv, "o-", color="#2D6A4F", linewidth=2.5, markersize=10, zorder=3,
            label="C_v Coherence")

    # Highlight peak
    ax.scatter([best_k], [best_cv], s=200, color="#E63946", zorder=5,
               edgecolors="black", linewidths=2, label=f"Optimal K={best_k}")
    ax.axvline(x=best_k, color="#E63946", linestyle="--", linewidth=1, alpha=0.5)

    # Annotate values
    for k, v in zip(ks, cv):
        weight = "bold" if k == best_k else "normal"
        color = "#E63946" if k == best_k else "#333333"
        ax.annotate(f"{v:.4f}", (k, v), textcoords="offset points",
                    xytext=(0, 15), ha="center", fontsize=11,
                    fontweight=weight, color=color)

    ax.set_xlabel("Number of Topics (K)", fontsize=13)
    ax.set_ylabel("C_v Coherence Score", fontsize=13)
    ax.set_title("LDA Topic Coherence (C_v) vs. Number of Topics",
                 fontsize=14, fontweight="bold")
    ax.set_xticks(ks)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%d"))
    ax.legend(fontsize=11, loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(min(cv) - 0.015, max(cv) + 0.025)

    # Add note
    ax.text(0.98, 0.02,
            "C_v measures semantic similarity among top words per topic\n"
            "Higher = more coherent and interpretable topics",
            transform=ax.transAxes, fontsize=9, ha="right", va="bottom",
            fontstyle="italic", color="#666666",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5", edgecolor="#cccccc"))

    plt.tight_layout()

    output = FIGURES_DIR / "part3_cv_coherence_k_selection.png"
    plt.savefig(output, dpi=200, bbox_inches="tight")
    print(f"Saved: {output}")
    plt.close()

    return output


def main():
    print("=" * 55)
    print("LDA K Selection Visualization")
    print("=" * 55)

    ks, cv, umass, perplexity_proxy = load_scores()

    print(f"\nLoaded scores for K = {ks}")
    print(f"  C_v:       {[f'{v:.4f}' for v in cv]}")
    print(f"  U_MASS:    {[f'{v:.4f}' for v in umass]}")
    print(f"  Perplexity: {[f'{v:.1f}' for v in perplexity_proxy]}")

    # 3-panel comparison
    plot_k_selection(ks, cv, umass, perplexity_proxy)

    # Standalone C_v for paper
    plot_cv_detail(ks, cv)

    print("\nDone.")


if __name__ == "__main__":
    main()
