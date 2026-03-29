"""
04 — Seasonal & Temporal Patterns
====================================
Monthly trends, day-of-week patterns, hour-by-day heatmap,
weekly trend, and holiday-period analysis.

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
    PALETTE, thousands,
)


# =============================================================================
# Chart 1 — Monthly Delay Trend Line
# =============================================================================
def chart_monthly_trend(con):
    print("[1/5] Monthly delay trend line ...")
    monthly = con.execute("""
        SELECT
            month,
            AVG(arr_delay_minutes)  AS avg_delay,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            COUNT(*)                AS flights,
            AVG(dep_delay_minutes)  AS avg_dep_delay
        FROM flights
        GROUP BY month
        ORDER BY month
    """).fetchdf()
    month_map = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May"}
    monthly["label"] = monthly["month"].map(month_map)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly["label"], monthly["avg_delay"],
            color=NAVY, linewidth=2.5, marker="o", markersize=8, label="Arrival")
    ax.plot(monthly["label"], monthly["avg_dep_delay"],
            color=ACCENT, linewidth=2.5, marker="s", markersize=8, label="Departure")
    ax.fill_between(monthly["label"], monthly["avg_delay"],
                    monthly["avg_dep_delay"], alpha=0.08, color=NAVY)
    ax.set_ylabel("Average Delay (min)")
    ax.legend(fontsize=9)

    for _, row in monthly.iterrows():
        ax.text(row["label"], row["avg_delay"] + 0.4,
                f"{row['avg_delay']:.1f}", ha="center", fontsize=8,
                fontweight="bold", color=NAVY)

    format_chart(fig, ax,
                 "Both Departure and Arrival Delays Climb Into Spring",
                 "Monthly average delay in minutes | Jan-May 2023")
    save_chart(fig, "20_monthly_trend_line")
    print()


# =============================================================================
# Chart 2 — Day-of-Week Pattern
# =============================================================================
def chart_dow_pattern(con):
    print("[2/5] Day-of-week delay pattern ...")
    dow_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    dow = con.execute("""
        SELECT
            day_of_week,
            AVG(arr_delay_minutes)  AS avg_delay,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            COUNT(*)                AS flights
        FROM flights
        GROUP BY day_of_week
        ORDER BY day_of_week
    """).fetchdf()
    dow["day_name"] = dow["day_of_week"].map(dow_map)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Avg delay
    colors = [ACCENT if d in [5, 7] else NAVY for d in dow["day_of_week"]]
    ax1.bar(dow["day_name"], dow["avg_delay"], color=colors,
            edgecolor="white", width=0.55)
    ax1.set_ylabel("Avg Arrival Delay (min)")
    ax1.set_title("Average Delay", fontsize=11, color=GRAY_DARK)
    for i, r in dow.iterrows():
        ax1.text(i, r["avg_delay"] + 0.2, f"{r['avg_delay']:.1f}",
                 ha="center", fontsize=9, color=GRAY_DARK)

    # Flight volume
    ax2.bar(dow["day_name"], dow["flights"], color=BLUE_MED,
            edgecolor="white", width=0.55)
    ax2.set_ylabel("Flights")
    ax2.set_title("Flight Volume", fontsize=11, color=GRAY_DARK)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(thousands))

    format_chart(fig, [ax1, ax2],
                 "Fridays and Sundays Peak in Delays, Saturdays Are Calmest",
                 "Day-of-week patterns for average delay and flight volume")
    save_chart(fig, "21_dow_pattern")
    print()


# =============================================================================
# Chart 3 — Hour x Day Heatmap
# =============================================================================
def chart_hour_day_heatmap(con):
    print("[3/5] Hour x Day-of-Week heatmap ...")
    dow_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    heatmap_data = con.execute("""
        SELECT
            day_of_week,
            hour_of_day,
            AVG(arr_delay_minutes) AS avg_delay
        FROM flights
        GROUP BY day_of_week, hour_of_day
        ORDER BY day_of_week, hour_of_day
    """).fetchdf()

    pivot = heatmap_data.pivot(index="day_of_week", columns="hour_of_day",
                                values="avg_delay")
    pivot.index = pivot.index.map(dow_map)

    fig, ax = plt.subplots(figsize=(16, 5))
    im = ax.imshow(pivot.values, cmap="RdYlGn_r", aspect="auto")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Avg Delay (min)")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("")
    # Add annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=7, color="white" if val > pivot.values[~np.isnan(pivot.values)].mean() else "black")

    format_chart(fig, ax,
                 "Late-Evening Flights on Fridays and Sundays Are the Worst Combination",
                 "Average arrival delay (min) by hour of day and day of week")
    save_chart(fig, "22_hour_day_heatmap")
    print()


# =============================================================================
# Chart 4 — Weekly Trend (delay rate over time)
# =============================================================================
def chart_weekly_trend(con):
    print("[4/5] Weekly delay rate trend ...")
    weekly = con.execute("""
        SELECT
            DATE_TRUNC('week', flight_date)                   AS week_start,
            WEEKOFYEAR(flight_date)                           AS week_num,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            AVG(arr_delay_minutes)                             AS avg_delay,
            COUNT(*)                                           AS flights
        FROM flights
        GROUP BY DATE_TRUNC('week', flight_date), WEEKOFYEAR(flight_date)
        ORDER BY week_start
    """).fetchdf()

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(weekly["week_num"], weekly["delay_rate"] * 100,
                    alpha=0.2, color=NAVY)
    ax.plot(weekly["week_num"], weekly["delay_rate"] * 100,
            color=NAVY, linewidth=2, marker="o", markersize=3)

    # Highlight holiday-adjacent weeks
    holiday_weeks = {1: "New Year", 7: "Valentine's", 9: "Presidents' Day",
                     13: "Spring Break", 18: "Memorial Day"}
    for wk_num, label in holiday_weeks.items():
        if wk_num in weekly["week_num"].values:
            row = weekly[weekly["week_num"] == wk_num].iloc[0]
            ax.annotate(label,
                        xy=(wk_num, row["delay_rate"] * 100),
                        xytext=(0, 12), textcoords="offset points",
                        fontsize=7, color=ACCENT, fontweight="bold",
                        ha="center",
                        arrowprops=dict(arrowstyle="->", color=ACCENT, lw=0.8))

    ax.set_xlabel("Week Number (2023)")
    ax.set_ylabel("Delay Rate (%)")

    format_chart(fig, ax,
                 "Delay Rates Spike Around Holiday and Travel-Heavy Periods",
                 "Weekly delay rate with holiday-adjacent weeks annotated")
    save_chart(fig, "23_weekly_trend")
    print()


# =============================================================================
# Chart 5 — Holiday Period Analysis
# =============================================================================
def chart_holiday_periods(con):
    print("[5/5] Holiday period analysis ...")
    # Define approximate holiday windows in 2023
    holidays = {
        "New Year\n(Dec 31 - Jan 3)":     ("2023-01-01", "2023-01-03"),
        "MLK Weekend\n(Jan 13-16)":        ("2023-01-13", "2023-01-16"),
        "Presidents' Day\n(Feb 17-20)":    ("2023-02-17", "2023-02-20"),
        "Spring Break\n(Mar 10-19)":       ("2023-03-10", "2023-03-19"),
        "Memorial Day\n(May 26-29)":       ("2023-05-26", "2023-05-29"),
    }

    results = []
    for name, (start, end) in holidays.items():
        row = con.execute(f"""
            SELECT
                COUNT(*)                                           AS flights,
                AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
                AVG(arr_delay_minutes)                              AS avg_delay
            FROM flights
            WHERE flight_date >= '{start}' AND flight_date <= '{end}'
        """).fetchdf().iloc[0]
        if row["flights"] == 0:
            continue
        results.append({
            "period": name,
            "flights": int(row["flights"]),
            "delay_rate": row["delay_rate"],
            "avg_delay": row["avg_delay"],
        })

    # Overall baseline
    baseline = con.execute("""
        SELECT
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            AVG(arr_delay_minutes) AS avg_delay
        FROM flights
    """).fetchdf().iloc[0]
    baseline_rate = baseline["delay_rate"]

    if not results:
        print("  No holiday data found in date range.\n")
        return

    hol = pd.DataFrame(results)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(hol["period"], hol["delay_rate"] * 100,
                  color=NAVY, edgecolor="white", width=0.55)
    ax.axhline(baseline_rate * 100, color=ACCENT, linewidth=1.5,
               linestyle="--", label=f"Overall avg = {baseline_rate*100:.1f}%")
    ax.set_ylabel("Delay Rate (%)")
    ax.legend(fontsize=9)

    for bar, val in zip(bars, hol["delay_rate"] * 100):
        color = ACCENT if val > baseline_rate * 100 else NAVY
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                f"{val:.1f}%", ha="center", fontsize=9, fontweight="bold",
                color=color)

    format_chart(fig, ax,
                 "Holiday Travel Periods Show Elevated Delay Rates",
                 f"Delay rate during holiday windows vs overall average ({baseline_rate*100:.1f}%)")
    save_chart(fig, "24_holiday_periods")
    print()


# =============================================================================
# Main
# =============================================================================
def main():
    setup_mckinsey_style()
    con = get_connection()

    chart_monthly_trend(con)
    chart_dow_pattern(con)
    chart_hour_day_heatmap(con)
    chart_weekly_trend(con)
    chart_holiday_periods(con)

    con.close()
    print("Seasonal trends analysis complete. 5 charts saved to docs/charts/")


if __name__ == "__main__":
    main()
