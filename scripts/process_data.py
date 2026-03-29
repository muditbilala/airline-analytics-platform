"""
ETL Pipeline: Raw BTS Flight CSV -> Cleaned Parquet -> DuckDB Analytics Database

Reads flights_combined.csv (Jan-May 2023, ~2.76M rows), standardizes ALL CAPS
column names to snake_case, derives analytical columns, and loads into DuckDB
with reference/dimension tables.
"""

import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REFERENCE_DIR = BASE_DIR / "data" / "reference"
DUCKDB_PATH = PROCESSED_DIR / "flights.duckdb"

# ---------------------------------------------------------------------------
# Column rename mapping: ALL CAPS source -> snake_case target
# ---------------------------------------------------------------------------
COLUMN_RENAME = {
    "YEAR": "year",
    "MONTH": "month",
    "DAY_OF_MONTH": "day_of_month",
    "DAY_OF_WEEK": "day_of_week",
    "FL_DATE": "flight_date",
    "OP_UNIQUE_CARRIER": "carrier_code",
    "ORIGIN": "origin",
    "ORIGIN_CITY_NAME": "origin_city",
    "ORIGIN_STATE_ABR": "origin_state",
    "DEST": "dest",
    "DEST_CITY_NAME": "dest_city",
    "DEST_STATE_ABR": "dest_state",
    "CRS_DEP_TIME": "crs_dep_time",
    "DEP_TIME": "dep_time",
    "DEP_DELAY": "dep_delay",
    "DEP_DELAY_NEW": "dep_delay_minutes",
    "CRS_ARR_TIME": "crs_arr_time",
    "ARR_TIME": "arr_time",
    "ARR_DELAY": "arr_delay",
    "ARR_DELAY_NEW": "arr_delay_minutes",
    "CANCELLED": "cancelled",
    "CANCELLATION_CODE": "cancellation_code",
    "DISTANCE": "distance",
    "CARRIER_DELAY": "carrier_delay",
    "WEATHER_DELAY": "weather_delay",
    "NAS_DELAY": "nas_delay",
    "SECURITY_DELAY": "security_delay",
    "LATE_AIRCRAFT_DELAY": "late_aircraft_delay",
}

# ---------------------------------------------------------------------------
# Carrier code -> airline name lookup
# ---------------------------------------------------------------------------
CARRIER_NAMES = {
    "9E": "Endeavor Air",
    "AA": "American Airlines",
    "AS": "Alaska Airlines",
    "B6": "JetBlue Airways",
    "DL": "Delta Air Lines",
    "F9": "Frontier Airlines",
    "G4": "Allegiant Air",
    "HA": "Hawaiian Airlines",
    "MQ": "Envoy Air",
    "NK": "Spirit Airlines",
    "OH": "PSA Airlines",
    "OO": "SkyWest Airlines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "YX": "Republic Airways",
}


def process_flight_csv() -> pd.DataFrame:
    """Read the combined flight CSV, clean columns, derive fields, write Parquet."""
    csv_path = RAW_DIR / "flights" / "flights_combined.csv"

    if not csv_path.exists():
        print(f"ERROR: Flight data not found at {csv_path}")
        print("Please place flights_combined.csv in data/raw/flights/")
        sys.exit(1)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading {csv_path.name} ...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Raw shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    # Drop unnamed trailing columns (BTS sometimes adds empty columns)
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # ------------------------------------------------------------------
    # Rename ALL CAPS columns to snake_case
    # ------------------------------------------------------------------
    df = df.rename(columns={k: v for k, v in COLUMN_RENAME.items() if k in df.columns})

    # ------------------------------------------------------------------
    # Parse flight_date  (format: "3/1/2023 12:00:00 AM")
    # ------------------------------------------------------------------
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], format="mixed", dayfirst=False)

    # ------------------------------------------------------------------
    # Ensure numeric types for delay / time columns
    # ------------------------------------------------------------------
    numeric_cols = [
        "dep_delay", "dep_delay_minutes", "arr_delay", "arr_delay_minutes",
        "carrier_delay", "weather_delay", "nas_delay", "security_delay",
        "late_aircraft_delay", "crs_dep_time", "dep_time", "crs_arr_time",
        "arr_time", "distance", "cancelled",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ------------------------------------------------------------------
    # Derived columns
    # ------------------------------------------------------------------

    # arr_del15 / dep_del15 : 1 if delay >= 15 minutes, else 0
    df["arr_del15"] = (df["arr_delay"] >= 15).astype("Int64")
    df.loc[df["arr_delay"].isna(), "arr_del15"] = pd.NA
    df["dep_del15"] = (df["dep_delay"] >= 15).astype("Int64")
    df.loc[df["dep_delay"].isna(), "dep_del15"] = pd.NA

    # hour_of_day from scheduled departure time (HHMM format, e.g. 1430.0 -> 14)
    df["hour_of_day"] = (df["crs_dep_time"] // 100).clip(0, 23).astype("int64")

    # is_weekend (day_of_week: 1=Mon ... 7=Sun in BTS data; 6=Sat, 7=Sun)
    df["is_weekend"] = df["day_of_week"].isin([6, 7]).astype(int)

    # route (e.g. "ATL-LAX")
    df["route"] = df["origin"].astype(str) + "-" + df["dest"].astype(str)

    # quarter derived from month
    df["quarter"] = ((df["month"] - 1) // 3 + 1).astype("Int64")

    # is_delayed  (1 if arr_delay >= 15 for non-cancelled flights)
    df["is_delayed"] = np.where(
        (df["cancelled"] == 0) & (df["arr_delay"] >= 15), 1, 0
    )

    # primary_delay_cause — the category contributing the most delay minutes
    delay_cause_cols = [
        "carrier_delay", "weather_delay", "nas_delay",
        "security_delay", "late_aircraft_delay",
    ]
    cause_labels = {
        "carrier_delay": "Carrier",
        "weather_delay": "Weather",
        "nas_delay": "NAS",
        "security_delay": "Security",
        "late_aircraft_delay": "Late Aircraft",
    }
    existing_cause_cols = [c for c in delay_cause_cols if c in df.columns]
    if existing_cause_cols:
        cause_df = df[existing_cause_cols].fillna(0)
        max_col = cause_df.idxmax(axis=1)
        # Only assign cause when the flight is actually delayed (arr_del15 = 1)
        df["primary_delay_cause"] = max_col.map(cause_labels)
        df.loc[df["arr_del15"] != 1, "primary_delay_cause"] = None
        # Also null out if all cause columns are 0/null (delay with no breakdown)
        all_zero = (cause_df.sum(axis=1) == 0)
        df.loc[all_zero, "primary_delay_cause"] = None

    print(f"  Processed shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    # ------------------------------------------------------------------
    # Write to Parquet
    # ------------------------------------------------------------------
    parquet_path = PROCESSED_DIR / "flights.parquet"
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    parquet_size_mb = parquet_path.stat().st_size / (1024 * 1024)
    print(f"  Written to {parquet_path} ({parquet_size_mb:.1f} MB)")

    return df


def load_reference_data(con: duckdb.DuckDBPyConnection):
    """Load airport reference data (OurAirports format) into DuckDB."""
    airports_path = REFERENCE_DIR / "airports.csv"
    if airports_path.exists():
        print("Loading airport reference data...")
        con.execute("""
            CREATE OR REPLACE TABLE dim_airports AS
            SELECT
                iata_code,
                name        AS airport_name,
                latitude_deg  AS latitude,
                longitude_deg AS longitude,
                iso_country,
                iso_region,
                municipality AS city,
                type         AS airport_type
            FROM read_csv_auto(?, header=true, quote='"')
            WHERE iata_code IS NOT NULL
              AND TRIM(iata_code) != ''
        """, [str(airports_path)])
        count = con.execute("SELECT COUNT(*) FROM dim_airports").fetchone()[0]
        print(f"  Loaded {count:,} airports into dim_airports")
    else:
        print(f"WARNING: Airport data not found at {airports_path}")
        print("  Download from https://ourairports.com/data/airports.csv")


def load_carrier_dimension(con: duckdb.DuckDBPyConnection):
    """Create dim_carriers table from the static carrier name mapping."""
    print("Creating carrier dimension table...")
    rows = [(code, name) for code, name in CARRIER_NAMES.items()]
    con.execute("CREATE OR REPLACE TABLE dim_carriers (carrier_code VARCHAR, carrier_name VARCHAR)")
    con.executemany("INSERT INTO dim_carriers VALUES (?, ?)", rows)

    # Enrich with actual flight counts from the flights table
    con.execute("""
        CREATE OR REPLACE TABLE dim_carriers AS
        SELECT
            c.carrier_code,
            c.carrier_name,
            COALESCE(f.total_flights, 0) AS total_flights
        FROM dim_carriers c
        LEFT JOIN (
            SELECT carrier_code, COUNT(*) AS total_flights
            FROM flights
            GROUP BY carrier_code
        ) f USING (carrier_code)
        ORDER BY total_flights DESC
    """)
    count = con.execute("SELECT COUNT(*) FROM dim_carriers").fetchone()[0]
    print(f"  Loaded {count} carriers into dim_carriers")


def build_duckdb(flights_parquet: Path):
    """Create DuckDB database from Parquet file and reference data."""
    print(f"\nBuilding DuckDB database at {DUCKDB_PATH}...")

    con = duckdb.connect(str(DUCKDB_PATH))

    # Load main flights table from Parquet
    con.execute(f"""
        CREATE OR REPLACE TABLE flights AS
        SELECT * FROM read_parquet('{flights_parquet}')
    """)
    count = con.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
    print(f"  Loaded {count:,} flights into DuckDB")

    # Load reference / dimension data
    load_reference_data(con)
    load_carrier_dimension(con)

    # Create calendar dimension
    con.execute("""
        CREATE OR REPLACE TABLE dim_calendar AS
        SELECT DISTINCT
            flight_date,
            year,
            quarter,
            month,
            day_of_month,
            day_of_week,
            CASE WHEN day_of_week IN (6, 7) THEN 1 ELSE 0 END AS is_weekend,
            CASE
                WHEN month IN (12, 1, 2) THEN 'Winter'
                WHEN month IN (3, 4, 5)  THEN 'Spring'
                WHEN month IN (6, 7, 8)  THEN 'Summer'
                ELSE 'Fall'
            END AS season
        FROM flights
        ORDER BY flight_date
    """)
    print("  Created dim_calendar")

    # Run schema SQL to create views
    schema_path = BASE_DIR / "sql" / "00_schema.sql"
    if schema_path.exists():
        print("  Running 00_schema.sql (views)...")
        sql = schema_path.read_text()
        # DuckDB can execute multiple statements separated by semicolons
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                con.execute(stmt)

    con.close()
    db_size_mb = DUCKDB_PATH.stat().st_size / (1024 * 1024)
    print(f"\nDuckDB database ready: {db_size_mb:.1f} MB")


def print_data_quality_summary():
    """Quick data quality check after loading."""
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    print("\n" + "=" * 60)
    print("DATA QUALITY SUMMARY")
    print("=" * 60)

    # Row counts
    total = con.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
    print(f"\nTotal flights: {total:,}")

    # Date range
    date_range = con.execute(
        "SELECT MIN(flight_date), MAX(flight_date) FROM flights"
    ).fetchone()
    print(f"Date range: {date_range[0]} to {date_range[1]}")

    # Rows by month
    print("\nFlights by month:")
    for row in con.execute(
        "SELECT year, month, COUNT(*) AS cnt FROM flights GROUP BY year, month ORDER BY year, month"
    ).fetchall():
        print(f"  {row[0]}-{row[1]:02d}: {row[2]:,}")

    # Null percentages for key columns
    print("\nNull percentages (key columns):")
    null_checks = [
        "arr_delay", "dep_delay", "arr_delay_minutes", "dep_delay_minutes",
        "carrier_delay", "weather_delay", "cancelled", "origin", "dest",
    ]
    for col in null_checks:
        try:
            pct = con.execute(f"""
                SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE {col} IS NULL) / COUNT(*), 1)
                FROM flights
            """).fetchone()[0]
            print(f"  {col}: {pct}% null")
        except Exception:
            pass

    # Top 10 airports
    print("\nTop 10 airports by flight volume:")
    for row in con.execute("""
        SELECT origin, COUNT(*) AS cnt
        FROM flights GROUP BY origin ORDER BY cnt DESC LIMIT 10
    """).fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    # Delay rate
    delay_rate = con.execute("""
        SELECT ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1 ELSE 0 END), 1)
        FROM flights WHERE cancelled = 0
    """).fetchone()[0]
    print(f"\nOverall arrival delay rate (>=15 min): {delay_rate}%")

    # Carrier summary
    print("\nCarrier performance:")
    for row in con.execute("""
        SELECT
            f.carrier_code,
            c.carrier_name,
            COUNT(*) AS flights,
            ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 1) AS delay_pct
        FROM flights f
        LEFT JOIN dim_carriers c USING (carrier_code)
        WHERE f.cancelled = 0
        GROUP BY f.carrier_code, c.carrier_name
        ORDER BY flights DESC
        LIMIT 10
    """).fetchall():
        print(f"  {row[0]} ({row[1]}): {row[2]:,} flights, {row[3]}% delayed")

    con.close()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("AIRLINE FLIGHT DATA ETL PIPELINE")
    print("=" * 60)

    flights_df = process_flight_csv()
    parquet_path = PROCESSED_DIR / "flights.parquet"
    build_duckdb(parquet_path)
    print_data_quality_summary()

    print("\nETL pipeline complete. Data is ready for analysis.")
