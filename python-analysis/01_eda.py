"""
01 — Exploratory Data Analysis
================================
Comprehensive first look at the BTS flight delay dataset (Jan-May 2023).
Generates distribution plots, correlation matrices, missing-value analysis,
flight-volume trends, carrier delay rates, and dep-vs-arr scatter.

All heavy computation is pushed to DuckDB via SQL aggregations. Only small
result sets are pulled into Pandas for plotting.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors

# -- project imports ----------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.chart_styles import (
    setup_mckinsey_style, format_chart, save_chart, get_connection,
    NAVY, ACCENT, BLUE_MED, BLUE_LIGHT, GRAY_DARK, GRAY_MED,
    GRAY_LIGHT, PALETTE, SEQUENTIAL, thousands,
)


# =============================================================================
# Chart 1 — Delay Distribution (histogram + box approximation)
# =============================================================================
def chart_delay_distribution(con):
    print("[1/6] Delay distribution ...")

    # Get binned histogram data from DuckDB
    bins_df = con.execute("""
        SELECT FLOOR(arr_delay_minutes / 5) * 5 AS bin, COUNT(*) AS cnt
        FROM flights
        WHERE arr_delay_minutes IS NOT NULL
          AND arr_delay_minutes BETWEEN -60 AND 180
        GROUP BY bin
        ORDER BY bin
    """).fetchdf()

    # Get summary stats from DuckDB
    stats = con.execute("""
        SELECT
            AVG(arr_delay_minutes)                                      AS mean_delay,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY arr_delay_minutes) AS median_delay,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY arr_delay_minutes) AS p95_delay,
            MAX(arr_delay_minutes)                                      AS max_delay,
            COUNT(*)                                                     AS n
        FROM flights
        WHERE arr_delay_minutes IS NOT NULL
    """).fetchdf().iloc[0]

    # Get box-plot quantiles from DuckDB
    box = con.execute("""
        SELECT
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY arr_delay_minutes) AS q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY arr_delay_minutes) AS median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY arr_delay_minutes) AS q3,
            MIN(arr_delay_minutes)                                          AS minv,
            MAX(arr_delay_minutes)                                          AS maxv
        FROM flights
        WHERE arr_delay_minutes IS NOT NULL
          AND arr_delay_minutes BETWEEN -60 AND 180
    """).fetchdf().iloc[0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                    gridspec_kw={"width_ratios": [3, 1]})

    # Histogram from pre-aggregated bins
    ax1.bar(bins_df["bin"], bins_df["cnt"], width=4.5, color=NAVY,
            edgecolor="white", linewidth=0.3, alpha=0.9)
    ax1.axvline(stats["median_delay"], color=ACCENT, linestyle="--", linewidth=1.5,
                label=f"Median = {stats['median_delay']:.0f} min")
    ax1.axvline(stats["mean_delay"], color=BLUE_MED, linestyle="--", linewidth=1.5,
                label=f"Mean = {stats['mean_delay']:.1f} min")
    ax1.set_xlabel("Arrival Delay (minutes)")
    ax1.set_ylabel("Number of Flights")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(thousands))
    ax1.legend(fontsize=9)

    # Box plot from quantiles
    iqr = box["q3"] - box["q1"]
    whisker_lo = max(box["minv"], box["q1"] - 1.5 * iqr)
    whisker_hi = min(box["maxv"], box["q3"] + 1.5 * iqr)
    bp = ax2.bxp([{
        "med": box["median"],
        "q1": box["q1"],
        "q3": box["q3"],
        "whislo": whisker_lo,
        "whishi": whisker_hi,
        "fliers": [],
    }], patch_artist=True, widths=[0.5])
    bp["boxes"][0].set_facecolor(BLUE_LIGHT)
    bp["boxes"][0].set_edgecolor(NAVY)
    bp["medians"][0].set_color(ACCENT)
    bp["medians"][0].set_linewidth(2)
    for w in bp["whiskers"]:
        w.set_color(NAVY)
    for c in bp["caps"]:
        c.set_color(NAVY)
    ax2.set_ylabel("Minutes")
    ax2.set_xticklabels(["Arr Delay"])

    format_chart(fig, [ax1, ax2],
                 "Most Flights Arrive Close to On-Time, but the Tail Is Long",
                 f"Distribution of arrival delay (capped at 180 min) | N = {int(stats['n']):,}")
    save_chart(fig, "01_delay_distribution")

    print(f"  Mean delay:   {stats['mean_delay']:.1f} min")
    print(f"  Median delay: {stats['median_delay']:.0f} min")
    print(f"  95th pctile:  {stats['p95_delay']:.0f} min")
    print(f"  Max delay:    {stats['max_delay']:.0f} min\n")


# =============================================================================
# Chart 2 — Correlation Matrix
# =============================================================================
def chart_correlation(con):
    print("[2/6] Correlation matrix ...")
    # Sample a small set of rows for correlation
    sample = con.execute("""
        SELECT arr_delay_minutes, dep_delay_minutes, distance,
               carrier_delay, weather_delay, nas_delay,
               security_delay, late_aircraft_delay
        FROM flights
        USING SAMPLE 50000 ROWS
    """).fetchdf()

    corr = sample.corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    masked_corr = np.where(mask, np.nan, corr.values)
    im = ax.imshow(masked_corr, cmap="Blues", vmin=-1, vmax=1, aspect="auto")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(corr.columns, fontsize=9)
    # Add annotations
    for i in range(len(corr)):
        for j in range(len(corr)):
            if not mask[i, j]:
                ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                        fontsize=8, color="white" if abs(corr.iloc[i, j]) > 0.5 else "black")

    dep_arr_corr = corr.loc["dep_delay_minutes", "arr_delay_minutes"]
    format_chart(fig, ax,
                 f"Departure and Arrival Delays Are Highly Correlated (r = {dep_arr_corr:.2f})",
                 "Pearson correlation of numeric flight-level columns (50K sample)")
    save_chart(fig, "02_correlation_matrix")


# =============================================================================
# Chart 3 — Missing Value Analysis
# =============================================================================
def chart_missing_values(con):
    print("[3/6] Missing value analysis ...")
    # Compute null percentage per column via SQL
    total_rows = con.execute("SELECT COUNT(*) AS n FROM flights").fetchdf().iloc[0, 0]

    # Build dynamic SQL for each column's null count
    cols_df = con.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'flights'
        ORDER BY ordinal_position
    """).fetchdf()

    null_parts = []
    for col in cols_df["column_name"]:
        null_parts.append(
            f"SUM(CASE WHEN \"{col}\" IS NULL THEN 1 ELSE 0 END) AS \"{col}\""
        )

    null_query = f"SELECT {', '.join(null_parts)} FROM flights"
    null_counts = con.execute(null_query).fetchdf().iloc[0]

    missing_pct = (null_counts / total_rows * 100).sort_values(ascending=True)
    missing_pct = missing_pct[missing_pct > 0]

    if missing_pct.empty:
        print("  No missing values found.\n")
        return

    fig, ax = plt.subplots(figsize=(10, max(5, len(missing_pct) * 0.35)))
    bars = ax.barh(missing_pct.index, missing_pct.values, color=NAVY,
                   edgecolor="white", height=0.6)
    ax.set_xlabel("% Missing")
    ax.set_xlim(0, min(missing_pct.max() * 1.15, 100))

    for bar, val in zip(bars, missing_pct.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9, color=GRAY_DARK)

    format_chart(fig, ax,
                 "Delay-Cause Fields Are Missing for Non-Delayed Flights",
                 "Percentage of NULL values per column (only columns with > 0%)")
    save_chart(fig, "03_missing_values")

    print(f"  {len(missing_pct)} columns have missing values.")
    print(f"  Highest: {missing_pct.index[-1]} at {missing_pct.iloc[-1]:.1f}%\n")


# =============================================================================
# Chart 4 — Flight Volume Over Time
# =============================================================================
def chart_volume_over_time(con):
    print("[4/6] Flight volume over time ...")
    daily = con.execute("""
        SELECT flight_date, COUNT(*) AS flights
        FROM flights
        GROUP BY flight_date
        ORDER BY flight_date
    """).fetchdf()
    daily["flight_date"] = pd.to_datetime(daily["flight_date"])
    daily["ma7"] = daily["flights"].rolling(7, center=True).mean()

    total_flights = daily["flights"].sum()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(daily["flight_date"], daily["flights"],
                    alpha=0.25, color=BLUE_LIGHT)
    ax.plot(daily["flight_date"], daily["flights"],
            linewidth=0.5, color=BLUE_LIGHT, alpha=0.6, label="Daily")
    ax.plot(daily["flight_date"], daily["ma7"],
            linewidth=2, color=NAVY, label="7-day moving avg")
    ax.set_ylabel("Flights per Day")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(thousands))
    ax.legend(fontsize=9)

    format_chart(fig, ax,
                 "Daily Flight Volume Peaks in Spring with Weekend Dips",
                 f"Total flights: {total_flights:,} | Period: Jan - May 2023")
    save_chart(fig, "05_volume_over_time")

    print(f"  Avg daily flights: {daily['flights'].mean():,.0f}")
    peak = daily.loc[daily['flights'].idxmax()]
    print(f"  Peak day: {peak['flight_date'].strftime('%Y-%m-%d')} ({peak['flights']:,})\n")


# =============================================================================
# Chart 5 — Delay Rate by Carrier
# =============================================================================
def chart_delay_rate_by_carrier(con):
    print("[5/6] Delay rate by carrier ...")
    carrier = con.execute("""
        SELECT
            f.carrier_code,
            COUNT(*)                                          AS total,
            SUM(CASE WHEN f.is_delayed = 1 THEN 1 ELSE 0 END) AS delayed,
            AVG(CASE WHEN f.is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate
        FROM flights f
        GROUP BY f.carrier_code
        ORDER BY delay_rate ASC
    """).fetchdf()

    fig, ax = plt.subplots(figsize=(10, 7))
    median_rate = carrier["delay_rate"].median()
    colors = [ACCENT if r > median_rate else NAVY for r in carrier["delay_rate"]]
    bars = ax.barh(carrier["carrier_code"], carrier["delay_rate"],
                   color=colors, edgecolor="white", height=0.6)
    ax.set_xlabel("Delay Rate")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

    for bar, val in zip(bars, carrier["delay_rate"]):
        ax.text(val + 0.003, bar.get_y() + bar.get_height() / 2,
                f"{val:.1%}", va="center", fontsize=9, color=GRAY_DARK)

    avg = carrier["delay_rate"].mean()
    ax.axvline(avg, color=GRAY_MED, linestyle="--", linewidth=1,
               label=f"Avg = {avg:.1%}")
    ax.legend(fontsize=9)

    format_chart(fig, ax,
                 "Delay Rates Vary Widely Across Carriers",
                 "Share of flights with arrival delay >= 15 minutes")
    save_chart(fig, "06_delay_rate_by_carrier")

    best = carrier.iloc[0]
    worst = carrier.iloc[-1]
    print(f"  Best:  {best['carrier_code']} ({best['delay_rate']:.1%})")
    print(f"  Worst: {worst['carrier_code']} ({worst['delay_rate']:.1%})\n")


# =============================================================================
# Chart 6 — Departure Delay vs Arrival Delay Scatter
# =============================================================================
def chart_dep_vs_arr(con):
    print("[6/6] Dep delay vs Arr delay scatter ...")
    sample = con.execute("""
        SELECT dep_delay_minutes, arr_delay_minutes
        FROM flights
        WHERE dep_delay_minutes IS NOT NULL
          AND arr_delay_minutes IS NOT NULL
        USING SAMPLE 5000 ROWS
    """).fetchdf()

    # Get correlation from a larger sample for accuracy
    corr_val = con.execute("""
        SELECT CORR(dep_delay_minutes, arr_delay_minutes) AS r
        FROM flights
        WHERE dep_delay_minutes IS NOT NULL
          AND arr_delay_minutes IS NOT NULL
    """).fetchdf().iloc[0, 0]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(sample["dep_delay_minutes"], sample["arr_delay_minutes"],
               s=3, alpha=0.15, color=NAVY, rasterized=True)
    lim = max(sample["dep_delay_minutes"].quantile(0.99),
              sample["arr_delay_minutes"].quantile(0.99))
    ax.plot([0, lim], [0, lim], color=ACCENT, linewidth=1.2,
            linestyle="--", label="y = x")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Departure Delay (min)")
    ax.set_ylabel("Arrival Delay (min)")
    ax.set_aspect("equal")
    ax.legend(fontsize=9)

    format_chart(fig, ax,
                 f"Late Departures Almost Always Mean Late Arrivals (r = {corr_val:.2f})",
                 "Random sample of 5,000 flights | dashed line = parity")
    save_chart(fig, "07_dep_vs_arr_scatter")
    print(f"  Correlation: {corr_val:.3f}\n")


# =============================================================================
# Main
# =============================================================================
def main():
    setup_mckinsey_style()
    con = get_connection()

    # Quick overview via SQL
    overview = con.execute("""
        SELECT
            COUNT(*)                        AS rows,
            MIN(flight_date)                AS date_min,
            MAX(flight_date)                AS date_max,
            COUNT(DISTINCT carrier_code)    AS carriers,
            COUNT(DISTINCT origin)          AS origins,
            COUNT(DISTINCT dest)            AS dests,
            SUM(cancelled)                  AS cancelled,
            AVG(cancelled) * 100            AS cancel_pct,
            SUM(is_delayed)                 AS delayed,
            AVG(is_delayed) * 100           AS delay_pct
        FROM flights
    """).fetchdf().iloc[0]

    ncols = con.execute("""
        SELECT COUNT(*) AS n FROM information_schema.columns
        WHERE table_name = 'flights'
    """).fetchdf().iloc[0, 0]

    print("=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)
    print(f"  Rows:    {int(overview['rows']):,}")
    print(f"  Columns: {int(ncols)}")
    print(f"  Date range: {overview['date_min']} to {overview['date_max']}")
    print(f"  Carriers:   {int(overview['carriers'])}")
    print(f"  Airports:   {int(overview['origins'])} origins, {int(overview['dests'])} destinations")
    print(f"  Cancelled:  {int(overview['cancelled']):,} ({overview['cancel_pct']:.1f}%)")
    print(f"  Delayed:    {int(overview['delayed']):,} ({overview['delay_pct']:.1f}%)")
    print("=" * 60 + "\n")

    chart_delay_distribution(con)
    chart_correlation(con)
    chart_missing_values(con)
    chart_volume_over_time(con)
    chart_delay_rate_by_carrier(con)
    chart_dep_vs_arr(con)

    con.close()
    print("EDA complete. 6 charts saved to docs/charts/")


if __name__ == "__main__":
    main()
