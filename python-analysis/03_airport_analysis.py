"""
03 — Airport Performance Analysis
====================================
Busiest and most-delayed airports, efficiency scoring, hub comparisons,
and a geographic scatter plot approximating a heatmap.

All heavy computation is pushed to DuckDB via SQL aggregations. Only small
result sets are pulled into Pandas for plotting.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.chart_styles import (
    setup_mckinsey_style, format_chart, save_chart, get_connection,
    NAVY, ACCENT, BLUE_MED, BLUE_LIGHT, GRAY_DARK, GRAY_MED,
    GRAY_LIGHT, PALETTE, thousands,
)


# =============================================================================
# Chart 1 — Top 20 Busiest Airports
# =============================================================================
def chart_busiest(con):
    print("[1/5] Top 20 busiest airports ...")
    top20 = con.execute("""
        WITH deps AS (
            SELECT origin AS airport, COUNT(*) AS departures FROM flights GROUP BY origin
        ),
        arrs AS (
            SELECT dest AS airport, COUNT(*) AS arrivals FROM flights GROUP BY dest
        ),
        combined AS (
            SELECT
                COALESCE(d.airport, a.airport)          AS airport,
                COALESCE(d.departures, 0)               AS departures,
                COALESCE(a.arrivals, 0)                 AS arrivals,
                COALESCE(d.departures, 0) + COALESCE(a.arrivals, 0) AS total
            FROM deps d
            FULL OUTER JOIN arrs a ON d.airport = a.airport
        )
        SELECT * FROM combined
        ORDER BY total DESC
        LIMIT 20
    """).fetchdf()

    # Sort ascending for horizontal bar chart (top at top)
    top20 = top20.sort_values("total", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(top20["airport"], top20["departures"], color=NAVY,
            label="Departures", edgecolor="white", height=0.6)
    ax.barh(top20["airport"], top20["arrivals"], left=top20["departures"],
            color=BLUE_LIGHT, label="Arrivals", edgecolor="white", height=0.6)
    ax.set_xlabel("Total Flights")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(thousands))
    ax.legend(fontsize=9)

    format_chart(fig, ax,
                 "ATL, DFW, and DEN Handle the Most Traffic",
                 "Top 20 airports by combined departures + arrivals | Jan-May 2023")
    save_chart(fig, "15_busiest_airports")

    print(f"  #1: {top20.iloc[-1]['airport']} with {int(top20.iloc[-1]['total']):,} flights\n")


# =============================================================================
# Chart 2 — Top 20 Most Delayed Airports
# =============================================================================
def chart_most_delayed(con):
    print("[2/5] Top 20 most delayed airports ...")
    top20 = con.execute("""
        SELECT
            origin,
            COUNT(*)                                           AS flights,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            AVG(arr_delay_minutes)                              AS avg_delay
        FROM flights
        GROUP BY origin
        HAVING COUNT(*) >= 5000
        ORDER BY delay_rate DESC
        LIMIT 20
    """).fetchdf()

    top20 = top20.sort_values("delay_rate", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = [ACCENT if r > 0.25 else NAVY for r in top20["delay_rate"]]
    bars = ax.barh(top20["origin"], top20["delay_rate"],
                   color=colors, edgecolor="white", height=0.6)
    ax.set_xlabel("Delay Rate")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

    for bar, val in zip(bars, top20["delay_rate"]):
        ax.text(val + 0.003, bar.get_y() + bar.get_height() / 2,
                f"{val:.1%}", va="center", fontsize=9, color=GRAY_DARK)

    format_chart(fig, ax,
                 "EWR and ORD Lead in Delay Rates Among Major Airports",
                 "Airports with >= 5,000 flights | delay = arrival >= 15 min late")
    save_chart(fig, "16_most_delayed_airports")
    print()


# =============================================================================
# Chart 3 — Efficiency Scatter (Volume vs Delay Rate)
# =============================================================================
def chart_efficiency_scatter(con):
    print("[3/5] Airport efficiency scatter ...")
    airport = con.execute("""
        SELECT
            origin,
            COUNT(*)                                           AS flights,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            AVG(arr_delay_minutes)                              AS avg_delay
        FROM flights
        GROUP BY origin
        HAVING COUNT(*) >= 2000
    """).fetchdf()

    fig, ax = plt.subplots(figsize=(11, 8))
    scatter = ax.scatter(airport["flights"], airport["delay_rate"],
                         s=airport["avg_delay"] * 8,
                         c=airport["avg_delay"],
                         cmap="RdYlBu_r", alpha=0.7, edgecolors=NAVY,
                         linewidths=0.5)
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.7)
    cbar.set_label("Avg Delay (min)", fontsize=9)

    ax.set_xlabel("Total Departures")
    ax.set_ylabel("Delay Rate")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(thousands))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

    # Label top airports
    for _, row in airport.nlargest(10, "flights").iterrows():
        ax.annotate(row["origin"], (row["flights"], row["delay_rate"]),
                    fontsize=8, fontweight="bold", color=GRAY_DARK,
                    xytext=(5, 5), textcoords="offset points")

    # Quadrant lines
    med_flights = airport["flights"].median()
    med_rate = airport["delay_rate"].median()
    ax.axhline(med_rate, color=GRAY_LIGHT, linewidth=1, linestyle="--")
    ax.axvline(med_flights, color=GRAY_LIGHT, linewidth=1, linestyle="--")

    format_chart(fig, ax,
                 "High-Volume Hubs Tend to Have Higher Delay Rates",
                 "Bubble size = avg delay | Color = avg delay | Dashed = median lines")
    save_chart(fig, "17_airport_efficiency")
    print()


# =============================================================================
# Chart 4 — Major Hub Comparison
# =============================================================================
def chart_hub_comparison(con):
    print("[4/5] Hub airport comparison ...")
    hubs = ["ATL", "ORD", "DFW", "DEN", "LAX", "CLT", "SFO", "JFK",
            "SEA", "EWR", "MIA", "IAH", "PHX", "BOS", "MSP"]
    hubs_sql = ", ".join(f"'{h}'" for h in hubs)

    hub_data = con.execute(f"""
        SELECT
            origin,
            COUNT(*)                                           AS flights,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            AVG(arr_delay_minutes)                              AS avg_delay,
            AVG(dep_delay_minutes)                              AS avg_dep_delay,
            AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END) AS cancel_rate
        FROM flights
        WHERE origin IN ({hubs_sql})
        GROUP BY origin
        ORDER BY delay_rate DESC
    """).fetchdf()

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    # Delay rate
    colors = [ACCENT if r > hub_data["delay_rate"].median() else NAVY
              for r in hub_data["delay_rate"]]
    axes[0].barh(hub_data["origin"], hub_data["delay_rate"],
                 color=colors, edgecolor="white", height=0.55)
    axes[0].set_title("Delay Rate", fontsize=11, color=GRAY_DARK)
    axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

    # Average delay
    axes[1].barh(hub_data["origin"], hub_data["avg_delay"],
                 color=BLUE_MED, edgecolor="white", height=0.55)
    axes[1].set_title("Avg Arrival Delay (min)", fontsize=11, color=GRAY_DARK)

    # Cancellation rate
    axes[2].barh(hub_data["origin"], hub_data["cancel_rate"] * 100,
                 color=ACCENT, edgecolor="white", height=0.55)
    axes[2].set_title("Cancellation Rate (%)", fontsize=11, color=GRAY_DARK)

    format_chart(fig, axes.tolist(),
                 "EWR and ORD Are the Most Delay-Prone Major Hubs",
                 "Performance comparison of 15 major US airport hubs | Jan-May 2023")
    save_chart(fig, "18_hub_comparison")
    print()


# =============================================================================
# Chart 5 — Geographic Scatter (pseudo-heatmap)
# =============================================================================
def chart_geographic(con):
    print("[5/5] Geographic delay map ...")
    geo = con.execute("""
        SELECT
            f.origin,
            COUNT(*)                                           AS flights,
            AVG(CASE WHEN f.is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            AVG(f.arr_delay_minutes)                            AS avg_delay,
            a.longitude,
            a.latitude
        FROM flights f
        LEFT JOIN dim_airports a ON f.origin = a.iata_code
        WHERE a.longitude IS NOT NULL AND a.latitude IS NOT NULL
        GROUP BY f.origin, a.longitude, a.latitude
        HAVING COUNT(*) >= 500
           AND a.longitude > -130 AND a.longitude < -65
           AND a.latitude > 24 AND a.latitude < 50
        ORDER BY flights DESC
    """).fetchdf()

    fig, ax = plt.subplots(figsize=(14, 8))
    scatter = ax.scatter(
        geo["longitude"], geo["latitude"],
        s=geo["flights"] / 150,
        c=geo["delay_rate"],
        cmap="RdYlGn_r",
        alpha=0.75,
        edgecolors=NAVY,
        linewidths=0.4,
        vmin=0.1, vmax=0.35,
    )
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Delay Rate", fontsize=9)

    # Label major airports
    for _, row in geo.nlargest(12, "flights").iterrows():
        ax.annotate(row["origin"],
                    (row["longitude"], row["latitude"]),
                    fontsize=7, fontweight="bold", color=GRAY_DARK,
                    xytext=(6, 6), textcoords="offset points")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect(1.3)

    format_chart(fig, ax,
                 "Northeast Corridor Airports Show the Highest Delay Rates",
                 "Bubble size = flight volume | Color = delay rate | Continental US airports with 500+ flights")
    save_chart(fig, "19_geographic_delay_map")
    print()


# =============================================================================
# Main
# =============================================================================
def main():
    setup_mckinsey_style()
    con = get_connection()

    chart_busiest(con)
    chart_most_delayed(con)
    chart_efficiency_scatter(con)
    chart_hub_comparison(con)
    chart_geographic(con)

    con.close()
    print("Airport analysis complete. 5 charts saved to docs/charts/")


if __name__ == "__main__":
    main()
