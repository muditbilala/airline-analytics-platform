"""
06 — Export Analytics to Excel Dashboard
==========================================
Query DuckDB for summary metrics and export a multi-sheet Excel workbook
formatted for business consumption.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.chart_styles import get_connection, BASE_DIR


EXCEL_DIR = BASE_DIR / "dashboard" / "excel"
EXCEL_PATH = EXCEL_DIR / "airline_analytics.xlsx"


# =============================================================================
# Helpers
# =============================================================================
def _auto_fit_columns(writer, sheet_name, df):
    """Set column widths based on max content length."""
    worksheet = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns):
        max_len = max(
            df[col].astype(str).map(len).max(),
            len(str(col))
        ) + 3
        worksheet.set_column(i, i, min(max_len, 40))


def _header_format(workbook):
    """Return a bold header format."""
    return workbook.add_format({
        "bold": True,
        "bg_color": "#1B3A5C",
        "font_color": "#FFFFFF",
        "border": 1,
        "text_wrap": True,
        "valign": "vcenter",
    })


def _write_sheet(writer, df, sheet_name, workbook, hdr_fmt):
    """Write a DataFrame to a sheet with formatted headers."""
    df.to_excel(writer, sheet_name=sheet_name, startrow=1, index=False,
                header=False)
    worksheet = writer.sheets[sheet_name]
    for col_num, value in enumerate(df.columns):
        worksheet.write(0, col_num, value, hdr_fmt)
    _auto_fit_columns(writer, sheet_name, df)


# =============================================================================
# Data queries
# =============================================================================
def query_summary(con):
    """KPI overview."""
    print("  [1/6] Summary KPIs ...")
    df = con.execute("""
        SELECT
            COUNT(*)                                           AS total_flights,
            SUM(is_delayed)                                    AS delayed_flights,
            ROUND(AVG(is_delayed) * 100, 2)                    AS delay_rate_pct,
            SUM(cancelled)                                     AS cancelled_flights,
            ROUND(AVG(cancelled) * 100, 2)                     AS cancel_rate_pct,
            ROUND(AVG(arr_delay_minutes), 2)                   AS avg_arrival_delay_min,
            ROUND(AVG(dep_delay_minutes), 2)                   AS avg_departure_delay_min,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
                (ORDER BY arr_delay_minutes), 2)               AS median_arrival_delay_min,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP
                (ORDER BY arr_delay_minutes), 2)               AS p95_arrival_delay_min,
            COUNT(DISTINCT carrier_code)                       AS carriers,
            COUNT(DISTINCT origin)                             AS origin_airports,
            MIN(flight_date)                                   AS date_start,
            MAX(flight_date)                                   AS date_end
        FROM flights
    """).fetchdf()
    return df.T.reset_index().rename(columns={"index": "Metric", 0: "Value"})


def query_hourly(con):
    """Hour-level aggregation."""
    print("  [2/6] Hourly delays ...")
    return con.execute("""
        SELECT
            hour_of_day                             AS hour,
            COUNT(*)                                AS flights,
            SUM(is_delayed)                         AS delayed,
            ROUND(AVG(is_delayed) * 100, 2)         AS delay_rate_pct,
            ROUND(AVG(arr_delay_minutes), 2)        AS avg_arr_delay_min,
            ROUND(AVG(dep_delay_minutes), 2)        AS avg_dep_delay_min
        FROM flights
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """).fetchdf()


def query_carrier(con):
    """Carrier-level metrics."""
    print("  [3/6] Carrier performance ...")
    return con.execute("""
        SELECT
            f.carrier_code,
            c.carrier_name,
            COUNT(*)                                AS flights,
            SUM(f.is_delayed)                       AS delayed,
            ROUND(AVG(f.is_delayed) * 100, 2)       AS delay_rate_pct,
            ROUND(AVG(f.arr_delay_minutes), 2)      AS avg_arr_delay_min,
            ROUND(AVG(f.dep_delay_minutes), 2)      AS avg_dep_delay_min,
            SUM(f.cancelled)                        AS cancelled,
            ROUND(AVG(f.cancelled) * 100, 2)         AS cancel_rate_pct,
            ROUND(AVG(f.carrier_delay), 2)          AS avg_carrier_delay,
            ROUND(AVG(f.weather_delay), 2)          AS avg_weather_delay,
            ROUND(AVG(f.nas_delay), 2)              AS avg_nas_delay,
            ROUND(AVG(f.late_aircraft_delay), 2)    AS avg_late_aircraft_delay
        FROM flights f
        LEFT JOIN dim_carriers c USING (carrier_code)
        GROUP BY f.carrier_code, c.carrier_name
        ORDER BY delay_rate_pct DESC
    """).fetchdf()


def query_airport(con):
    """Airport-level metrics."""
    print("  [4/6] Airport performance ...")
    return con.execute("""
        SELECT
            f.origin                                AS airport,
            a.airport_name,
            a.city,
            a.iso_region                            AS state,
            COUNT(*)                                AS departures,
            SUM(f.is_delayed)                       AS delayed,
            ROUND(AVG(f.is_delayed) * 100, 2)       AS delay_rate_pct,
            ROUND(AVG(f.arr_delay_minutes), 2)      AS avg_arr_delay_min,
            SUM(f.cancelled)                        AS cancelled,
            ROUND(AVG(f.cancelled) * 100, 2)         AS cancel_rate_pct
        FROM flights f
        LEFT JOIN dim_airports a ON f.origin = a.iata_code
        GROUP BY f.origin, a.airport_name, a.city, a.iso_region
        HAVING COUNT(*) >= 100
        ORDER BY departures DESC
    """).fetchdf()


def query_monthly(con):
    """Month-level time series."""
    print("  [5/6] Monthly trends ...")
    return con.execute("""
        SELECT
            month,
            COUNT(*)                                AS flights,
            SUM(is_delayed)                         AS delayed,
            ROUND(AVG(is_delayed) * 100, 2)         AS delay_rate_pct,
            ROUND(AVG(arr_delay_minutes), 2)        AS avg_arr_delay_min,
            ROUND(AVG(dep_delay_minutes), 2)        AS avg_dep_delay_min,
            SUM(cancelled)                          AS cancelled,
            ROUND(AVG(cancelled) * 100, 2)           AS cancel_rate_pct
        FROM flights
        GROUP BY month
        ORDER BY month
    """).fetchdf()


def query_delay_causes(con):
    """Delay cause breakdown."""
    print("  [6/6] Delay causes ...")
    return con.execute("""
        SELECT
            carrier_code,
            COUNT(*)                                                    AS delayed_flights,
            ROUND(SUM(carrier_delay), 0)                                AS total_carrier_delay_min,
            ROUND(SUM(weather_delay), 0)                                AS total_weather_delay_min,
            ROUND(SUM(nas_delay), 0)                                    AS total_nas_delay_min,
            ROUND(SUM(security_delay), 0)                               AS total_security_delay_min,
            ROUND(SUM(late_aircraft_delay), 0)                          AS total_late_aircraft_delay_min,
            ROUND(AVG(carrier_delay), 2)                                AS avg_carrier_delay,
            ROUND(AVG(weather_delay), 2)                                AS avg_weather_delay,
            ROUND(AVG(nas_delay), 2)                                    AS avg_nas_delay,
            ROUND(AVG(security_delay), 2)                               AS avg_security_delay,
            ROUND(AVG(late_aircraft_delay), 2)                          AS avg_late_aircraft_delay
        FROM flights
        WHERE is_delayed = 1
        GROUP BY carrier_code
        ORDER BY delayed_flights DESC
    """).fetchdf()


# =============================================================================
# Main
# =============================================================================
def main():
    EXCEL_DIR.mkdir(parents=True, exist_ok=True)

    con = get_connection()
    print("Querying DuckDB for Excel export ...\n")

    summary   = query_summary(con)
    hourly    = query_hourly(con)
    carrier   = query_carrier(con)
    airport   = query_airport(con)
    monthly   = query_monthly(con)
    causes    = query_delay_causes(con)
    con.close()

    print(f"\nWriting Excel workbook to {EXCEL_PATH.relative_to(BASE_DIR)} ...")

    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter") as writer:
        workbook = writer.book
        hdr_fmt = _header_format(workbook)

        _write_sheet(writer, summary,  "Summary",              workbook, hdr_fmt)
        _write_sheet(writer, hourly,   "Hourly_Delays",        workbook, hdr_fmt)
        _write_sheet(writer, carrier,  "Carrier_Performance",  workbook, hdr_fmt)
        _write_sheet(writer, airport,  "Airport_Performance",  workbook, hdr_fmt)
        _write_sheet(writer, monthly,  "Monthly_Trends",       workbook, hdr_fmt)
        _write_sheet(writer, causes,   "Delay_Causes",         workbook, hdr_fmt)

    print(f"  Workbook saved with {6} sheets.")
    print(f"  Path: {EXCEL_PATH}")
    print("\nExcel export complete.")


if __name__ == "__main__":
    main()
