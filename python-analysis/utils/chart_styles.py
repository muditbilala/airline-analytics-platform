"""
McKinsey-style chart formatting utilities for flight delay analytics.

Provides consistent, clean, professional styling for all matplotlib charts.
Design principles: minimal chart junk, clear hierarchy, insight-driven titles.
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------
NAVY       = "#1B3A5C"
ACCENT     = "#E85D3A"
BLUE_MED   = "#2E6B9E"
BLUE_LIGHT = "#5A9BD5"
GRAY_DARK  = "#4A4A4A"
GRAY_MED   = "#8C8C8C"
GRAY_LIGHT = "#D2D2D2"
GRAY_BG    = "#F5F5F5"
WHITE      = "#FFFFFF"

# Ordered palette for categorical series
PALETTE = [NAVY, ACCENT, BLUE_MED, BLUE_LIGHT, GRAY_DARK, "#F4A261",
           "#2A9D8F", "#E76F51", "#264653", "#E9C46A"]

# Diverging palette for heatmaps (light -> dark navy)
SEQUENTIAL = ["#F0F4F8", "#C5D5E4", "#8BACC8", "#5A9BD5", "#2E6B9E", NAVY]

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).resolve().parent.parent.parent   # project root
CHARTS_DIR = BASE_DIR / "docs" / "charts"
DB_PATH    = BASE_DIR / "data" / "processed" / "flights.duckdb"


def ensure_dirs():
    """Create output directories if they don't exist."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Global rcParams — call once at script start
# ---------------------------------------------------------------------------
def setup_mckinsey_style():
    """Apply McKinsey-inspired global matplotlib settings."""
    plt.rcParams.update({
        # Font
        "font.family":        "sans-serif",
        "font.sans-serif":    ["Helvetica Neue", "Helvetica", "Arial",
                               "DejaVu Sans"],
        "font.size":          11,
        # Axes
        "axes.titlesize":     14,
        "axes.titleweight":   "bold",
        "axes.titlecolor":    NAVY,
        "axes.labelsize":     11,
        "axes.labelcolor":    GRAY_DARK,
        "axes.edgecolor":     GRAY_LIGHT,
        "axes.linewidth":     0.6,
        "axes.facecolor":     WHITE,
        "axes.grid":          True,
        "axes.grid.axis":     "y",
        "axes.axisbelow":     True,
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        # Grid
        "grid.color":         GRAY_LIGHT,
        "grid.linewidth":     0.4,
        "grid.alpha":         0.7,
        # Ticks
        "xtick.color":        GRAY_DARK,
        "ytick.color":        GRAY_DARK,
        "xtick.labelsize":    10,
        "ytick.labelsize":    10,
        "xtick.major.size":   0,
        "ytick.major.size":   0,
        # Legend
        "legend.frameon":     False,
        "legend.fontsize":    10,
        # Figure
        "figure.facecolor":   WHITE,
        "figure.dpi":         150,
        "savefig.dpi":        200,
        "savefig.bbox":       "tight",
        "savefig.pad_inches": 0.3,
    })


# ---------------------------------------------------------------------------
# Per-chart formatting
# ---------------------------------------------------------------------------
def format_chart(fig, ax, title, subtitle="", source="Source: BTS On-Time Performance Data, Jan-May 2023"):
    """
    Apply McKinsey formatting to a single axes chart.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    ax  : matplotlib.axes.Axes  (or list of Axes for multi-panel)
    title : str – bold finding-driven title
    subtitle : str – descriptive detail line
    source : str – attribution line at bottom-left
    """
    # Title block
    fig.suptitle(title, x=0.04, y=0.98, ha="left", fontsize=14,
                 fontweight="bold", color=NAVY)
    if subtitle:
        fig.text(0.04, 0.935, subtitle, ha="left", fontsize=10,
                 color=GRAY_DARK, style="italic")

    # Source line
    fig.text(0.04, 0.01, source, ha="left", fontsize=7, color=GRAY_MED)

    # Clean up spines on all axes
    axes_list = [ax] if not isinstance(ax, (list, tuple)) else ax
    for a in axes_list:
        if hasattr(a, "flat"):
            for sub_a in a.flat:
                _clean_axis(sub_a)
        else:
            _clean_axis(a)

    fig.tight_layout(rect=[0, 0.03, 1, 0.92])


def _clean_axis(ax):
    """Remove chart junk from a single axis."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.4)
    ax.spines["bottom"].set_linewidth(0.4)
    ax.tick_params(axis="both", which="both", length=0)


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------
def save_chart(fig, name):
    """Save figure as PNG to docs/charts/<name>.png and close it."""
    ensure_dirs()
    path = CHARTS_DIR / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  -> Saved chart: {path.relative_to(BASE_DIR)}")


# ---------------------------------------------------------------------------
# Quick DuckDB connection helper
# ---------------------------------------------------------------------------
def get_connection():
    """Return a read-only DuckDB connection to the flights database."""
    import duckdb
    return duckdb.connect(str(DB_PATH), read_only=True)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def thousands(x, _=None):
    """Tick formatter: 1234567 -> '1,234,567'."""
    return f"{int(x):,}"

def pct_fmt(x, _=None):
    """Tick formatter: 0.1234 -> '12.3%'."""
    return f"{x*100:.1f}%"

def add_value_labels(ax, fmt="{:.1f}", fontsize=8, color=GRAY_DARK, offset=0.5):
    """Add value labels on top of bar charts."""
    for bar in ax.patches:
        val = bar.get_height()
        if val == 0:
            continue
        ax.text(bar.get_x() + bar.get_width() / 2, val + offset,
                fmt.format(val), ha="center", va="bottom",
                fontsize=fontsize, color=color)
