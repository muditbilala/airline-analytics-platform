"""
02 — Deep Delay Analysis
=========================
Drill into delay patterns: hourly profile, cause decomposition, carrier
comparison, severe delays, monthly trends, and weekend vs weekday.

All heavy computation is pushed to DuckDB via SQL aggregations. Only small
result sets (< 100 rows) are pulled into Pandas for plotting.
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
    GRAY_LIGHT, PALETTE, thousands, add_value_labels,
)


# =============================================================================
# Chart 1 — Delay by Hour of Day
# =============================================================================
def chart_hourly_delay(con):
    print("[1/7] Hourly delay profile ...")
    hourly = con.execute("""
        SELECT
            hour_of_day,
            AVG(arr_delay_minutes)  AS avg_delay,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            COUNT(*)                AS flights
        FROM flights
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """).fetchdf()

    fig, ax1 = plt.subplots(figsize=(13, 5))
    bars = ax1.bar(hourly["hour_of_day"], hourly["avg_delay"],
                   color=[ACCENT if h >= 17 else NAVY for h in hourly["hour_of_day"]],
                   edgecolor="white", width=0.7)
    ax1.set_xlabel("Scheduled Departure Hour")
    ax1.set_ylabel("Average Arrival Delay (min)", color=NAVY)
    ax1.set_xticks(range(0, 24))

    # Overlay delay rate on secondary axis
    ax2 = ax1.twinx()
    ax2.plot(hourly["hour_of_day"], hourly["delay_rate"] * 100,
             color=BLUE_MED, linewidth=2, marker="o", markersize=4, label="Delay rate %")
    ax2.set_ylabel("Delay Rate (%)", color=BLUE_MED)
    ax2.spines["top"].set_visible(False)
    ax2.tick_params(axis="y", colors=BLUE_MED)

    # Callout for worst hour
    worst = hourly.loc[hourly["avg_delay"].idxmax()]
    ax1.annotate(f"Peak: {worst['avg_delay']:.1f} min\nat {int(worst['hour_of_day'])}:00",
                 xy=(worst["hour_of_day"], worst["avg_delay"]),
                 xytext=(worst["hour_of_day"] - 4, worst["avg_delay"] + 3),
                 fontsize=9, color=ACCENT, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2))

    format_chart(fig, ax1,
                 "Delays Build Through the Day and Peak in Late Afternoon",
                 "Average arrival delay (bars) and delay rate (line) by scheduled departure hour")
    save_chart(fig, "08_hourly_delay_profile")

    print(f"  Worst hour: {int(worst['hour_of_day'])}:00 — avg {worst['avg_delay']:.1f} min\n")


# =============================================================================
# Chart 2 — Delay Cause Decomposition
# =============================================================================
def chart_delay_causes(con):
    print("[2/7] Delay cause decomposition ...")

    # Overall cause totals
    totals_df = con.execute("""
        SELECT
            COALESCE(SUM(carrier_delay), 0)        AS carrier_delay,
            COALESCE(SUM(weather_delay), 0)         AS weather_delay,
            COALESCE(SUM(nas_delay), 0)             AS nas_delay,
            COALESCE(SUM(security_delay), 0)        AS security_delay,
            COALESCE(SUM(late_aircraft_delay), 0)   AS late_aircraft_delay
        FROM flights
    """).fetchdf().iloc[0]

    causes = ["carrier_delay", "weather_delay", "nas_delay",
              "security_delay", "late_aircraft_delay"]
    labels = ["Carrier", "Weather", "NAS", "Security", "Late Aircraft"]
    totals = totals_df[causes]
    grand = totals.sum()

    # Stacked bar by carrier — avg cause delay per carrier
    carrier_causes = con.execute("""
        SELECT
            carrier_code,
            AVG(carrier_delay)        AS carrier_delay,
            AVG(weather_delay)        AS weather_delay,
            AVG(nas_delay)            AS nas_delay,
            AVG(security_delay)       AS security_delay,
            AVG(late_aircraft_delay)  AS late_aircraft_delay
        FROM flights
        GROUP BY carrier_code
        ORDER BY AVG(carrier_delay) DESC
    """).fetchdf().set_index("carrier_code")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                    gridspec_kw={"width_ratios": [2, 3]})
    # Pie chart
    colors_pie = [NAVY, ACCENT, BLUE_MED, GRAY_MED, BLUE_LIGHT]
    wedges, _, autotexts = ax1.pie(
        totals.values, labels=labels, colors=colors_pie,
        autopct="%1.1f%%", startangle=90, pctdistance=0.75,
        textprops={"fontsize": 9})
    for t in autotexts:
        t.set_color("white")
        t.set_fontweight("bold")

    # Stacked bar by carrier
    bottom = np.zeros(len(carrier_causes))
    for i, (col, lbl) in enumerate(zip(causes, labels)):
        ax2.bar(carrier_causes.index, carrier_causes[col], bottom=bottom,
                color=colors_pie[i], label=lbl, edgecolor="white", width=0.7)
        bottom += carrier_causes[col].values
    ax2.set_ylabel("Avg Delay Minutes (stacked)")
    ax2.set_xlabel("Carrier")
    ax2.legend(fontsize=8, ncol=3, loc="upper right")

    format_chart(fig, [ax1, ax2],
                 "Late Aircraft and Carrier Issues Drive Most Delay Minutes",
                 "Left: share of total delay minutes | Right: stacked avg delay per carrier")
    save_chart(fig, "09_delay_cause_decomposition")

    for lbl, val in zip(labels, totals.values):
        print(f"  {lbl:18s}: {val/1e6:.2f}M min ({val/grand*100:.1f}%)")
    print()


# =============================================================================
# Chart 3 — Delay Distribution by Carrier (percentile-based)
# =============================================================================
def chart_carrier_delay_dist(con):
    print("[3/7] Carrier delay distributions ...")

    # Get percentiles per carrier for delayed flights
    carrier_pctiles = con.execute("""
        SELECT
            carrier_code,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY arr_delay_minutes) AS q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY arr_delay_minutes) AS median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY arr_delay_minutes) AS q3,
            MIN(arr_delay_minutes) AS minv,
            MAX(CASE WHEN arr_delay_minutes <= 180 THEN arr_delay_minutes END) AS maxv,
            COUNT(*) AS n
        FROM flights
        WHERE is_delayed = 1 AND arr_delay_minutes <= 180
        GROUP BY carrier_code
        ORDER BY PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY arr_delay_minutes) DESC
    """).fetchdf()

    overall_median = con.execute("""
        SELECT PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY arr_delay_minutes) AS med
        FROM flights
        WHERE is_delayed = 1 AND arr_delay_minutes <= 180
    """).fetchdf().iloc[0, 0]

    fig, ax = plt.subplots(figsize=(14, 6))

    # Build box plot data from SQL percentiles
    bxp_data = []
    labels = []
    for _, row in carrier_pctiles.iterrows():
        iqr = row["q3"] - row["q1"]
        whislo = max(row["minv"], row["q1"] - 1.5 * iqr)
        whishi = min(row["maxv"], row["q3"] + 1.5 * iqr)
        bxp_data.append({
            "med": row["median"],
            "q1": row["q1"],
            "q3": row["q3"],
            "whislo": whislo,
            "whishi": whishi,
            "fliers": [],
        })
        labels.append(row["carrier_code"])

    bp = ax.bxp(bxp_data, patch_artist=True, widths=0.5)
    for box in bp["boxes"]:
        box.set_facecolor(BLUE_LIGHT)
        box.set_edgecolor(NAVY)
    for med in bp["medians"]:
        med.set_color(ACCENT)
        med.set_linewidth(1.5)
    for w in bp["whiskers"]:
        w.set_color(NAVY)
    for c in bp["caps"]:
        c.set_color(NAVY)

    ax.set_xticklabels(labels, fontsize=9)
    ax.set_xlabel("Carrier")
    ax.set_ylabel("Arrival Delay (min)")
    ax.axhline(overall_median, color=ACCENT, linestyle="--", linewidth=1,
               label=f"Overall median = {overall_median:.0f} min")
    ax.legend(fontsize=9)

    format_chart(fig, ax,
                 "Carrier Delay Distributions Vary Significantly",
                 "Distribution of arrival delay (delayed flights only, capped at 180 min)")
    save_chart(fig, "10_carrier_delay_distributions")
    print()


# =============================================================================
# Chart 4 — Severe Delays Analysis
# =============================================================================
def chart_severe_delays(con):
    print("[4/7] Severe delays analysis ...")
    severity = con.execute("""
        SELECT
            CASE
                WHEN arr_delay_minutes <= 0      THEN 'On-time / Early'
                WHEN arr_delay_minutes <= 15     THEN 'Minor (1-15)'
                WHEN arr_delay_minutes <= 60     THEN 'Moderate (16-60)'
                WHEN arr_delay_minutes <= 120    THEN 'Severe (61-120)'
                ELSE                                  'Extreme (>120)'
            END AS severity,
            COUNT(*) AS cnt
        FROM flights
        WHERE arr_delay_minutes IS NOT NULL
        GROUP BY severity
    """).fetchdf()

    # Enforce order
    order = ["On-time / Early", "Minor (1-15)", "Moderate (16-60)",
             "Severe (61-120)", "Extreme (>120)"]
    severity = severity.set_index("severity").reindex(order).reset_index()
    total = severity["cnt"].sum()
    severity["pct"] = severity["cnt"] / total * 100

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [NAVY, BLUE_LIGHT, BLUE_MED, ACCENT, "#C0392B"]
    bars = ax.bar(severity["severity"], severity["cnt"], color=colors,
                  edgecolor="white", width=0.65)
    ax.set_ylabel("Number of Flights")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(thousands))

    for bar, pct in zip(bars, severity["pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + total * 0.005,
                f"{pct:.1f}%", ha="center", fontsize=10, fontweight="bold",
                color=GRAY_DARK)

    severe_count = severity[severity["severity"].isin(["Severe (61-120)", "Extreme (>120)"])]["cnt"].sum()
    severe_pct = severe_count / total * 100

    format_chart(fig, ax,
                 f"{severe_count:,} Flights Had Severe or Extreme Delays",
                 "Arrival delay severity breakdown across all flights")
    save_chart(fig, "11_severe_delays")

    print(f"  Severe+Extreme: {severe_count:,} flights ({severe_pct:.1f}%)\n")


# =============================================================================
# Chart 5 — Delay Trends by Month
# =============================================================================
def chart_monthly_trends(con):
    print("[5/7] Monthly delay trends ...")
    monthly = con.execute("""
        SELECT
            month,
            AVG(arr_delay_minutes)  AS avg_delay,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            COUNT(*)                AS flights
        FROM flights
        GROUP BY month
        ORDER BY month
    """).fetchdf()
    month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May"}
    monthly["month_name"] = monthly["month"].map(month_names)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(monthly["month_name"], monthly["avg_delay"],
            color=NAVY, edgecolor="white", width=0.5, label="Avg delay (min)")
    ax1.set_ylabel("Average Arrival Delay (min)")

    ax2 = ax1.twinx()
    ax2.plot(monthly["month_name"], monthly["delay_rate"] * 100,
             color=ACCENT, linewidth=2.5, marker="D", markersize=7,
             label="Delay rate %")
    ax2.set_ylabel("Delay Rate (%)", color=ACCENT)
    ax2.spines["top"].set_visible(False)
    ax2.tick_params(axis="y", colors=ACCENT)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="upper left")

    format_chart(fig, ax1,
                 "Delay Performance Worsens Heading Into Summer",
                 "Monthly average arrival delay and delay rate | Jan-May 2023")
    save_chart(fig, "12_monthly_delay_trend")
    print()


# =============================================================================
# Chart 6 — Weekend vs Weekday
# =============================================================================
def chart_weekend_weekday(con):
    print("[6/7] Weekend vs weekday comparison ...")
    wk = con.execute("""
        SELECT
            is_weekend,
            AVG(arr_delay_minutes)  AS avg_delay,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
            COUNT(*)                AS flights,
            AVG(dep_delay_minutes)  AS avg_dep_delay
        FROM flights
        GROUP BY is_weekend
        ORDER BY is_weekend
    """).fetchdf()
    wk["label"] = wk["is_weekend"].map({0: "Weekday", 1: "Weekend"})

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # Flights
    axes[0].bar(wk["label"], wk["flights"], color=[NAVY, ACCENT],
                edgecolor="white", width=0.45)
    axes[0].set_title("Total Flights", fontsize=11, color=GRAY_DARK)
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(thousands))

    # Avg delay
    axes[1].bar(wk["label"], wk["avg_delay"], color=[NAVY, ACCENT],
                edgecolor="white", width=0.45)
    axes[1].set_title("Avg Arrival Delay (min)", fontsize=11, color=GRAY_DARK)

    # Delay rate
    axes[2].bar(wk["label"], wk["delay_rate"] * 100, color=[NAVY, ACCENT],
                edgecolor="white", width=0.45)
    axes[2].set_title("Delay Rate (%)", fontsize=11, color=GRAY_DARK)

    for ax, col in zip(axes, ["flights", "avg_delay", "delay_rate"]):
        for i, row in wk.iterrows():
            val = row[col] * 100 if col == "delay_rate" else row[col]
            fmt = f"{val:.1f}%" if col == "delay_rate" else (f"{val:,.0f}" if col == "flights" else f"{val:.1f}")
            ax.text(i, val + (val * 0.02 + 0.5), fmt,
                    ha="center", fontsize=10, fontweight="bold", color=GRAY_DARK)

    format_chart(fig, axes.tolist(),
                 "Weekdays See More Flights but Similar Delay Patterns",
                 "Weekday (Mon-Fri) vs Weekend (Sat-Sun) comparison")
    save_chart(fig, "13_weekend_vs_weekday")
    print()


# =============================================================================
# Chart 7 — Delay Rate by Day of Week
# =============================================================================
def chart_day_of_week(con):
    print("[7/7] Day-of-week delay pattern ...")
    dow = con.execute("""
        SELECT
            day_of_week,
            AVG(arr_delay_minutes)  AS avg_delay,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate
        FROM flights
        GROUP BY day_of_week
        ORDER BY day_of_week
    """).fetchdf()
    day_names = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    dow["day_name"] = dow["day_of_week"].map(day_names)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [ACCENT if d in [5, 7] else NAVY for d in dow["day_of_week"]]
    ax.bar(dow["day_name"], dow["avg_delay"], color=colors,
           edgecolor="white", width=0.55)
    ax.set_ylabel("Average Arrival Delay (min)")

    for i, row in dow.iterrows():
        ax.text(i, row["avg_delay"] + 0.3, f"{row['avg_delay']:.1f}",
                ha="center", fontsize=9, fontweight="bold", color=GRAY_DARK)

    format_chart(fig, ax,
                 "Fridays and Sundays Tend to Have the Highest Delays",
                 "Average arrival delay by day of week | highlighted = typically worse days")
    save_chart(fig, "14_day_of_week_delay")
    print()


# =============================================================================
# Main
# =============================================================================
def main():
    setup_mckinsey_style()
    con = get_connection()

    chart_hourly_delay(con)
    chart_delay_causes(con)
    chart_carrier_delay_dist(con)
    chart_severe_delays(con)
    chart_monthly_trends(con)
    chart_weekend_weekday(con)
    chart_day_of_week(con)

    con.close()
    print("Delay analysis complete. 7 charts saved to docs/charts/")


if __name__ == "__main__":
    main()
