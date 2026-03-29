-- ============================================================
-- SCHEMA: Airline Flight Delay Analytics
-- Database: DuckDB
-- Purpose: Define views on the flights table for common
--          aggregation patterns used by dashboards and notebooks
-- ============================================================
-- Depends on tables: flights, dim_airports, dim_carriers
-- Column reference (snake_case after ETL rename):
--   year, month, day_of_month, day_of_week, flight_date,
--   carrier_code, origin, origin_city, origin_state, dest,
--   dest_city, dest_state, crs_dep_time, dep_time, dep_delay,
--   dep_delay_minutes, crs_arr_time, arr_time, arr_delay,
--   arr_delay_minutes, cancelled, cancellation_code, distance,
--   carrier_delay, weather_delay, nas_delay, security_delay,
--   late_aircraft_delay
-- Derived: arr_del15, dep_del15, hour_of_day, is_weekend, route,
--          quarter, is_delayed, primary_delay_cause


-- ============================================================
-- VIEW 1: Daily airport-level aggregates
-- ============================================================
CREATE OR REPLACE VIEW v_daily_airport_summary AS
SELECT
    flight_date,
    origin                                          AS airport,
    year,
    month,
    day_of_week,
    COUNT(*)                                        AS total_flights,
    SUM(CASE WHEN cancelled = 1 THEN 1 ELSE 0 END) AS cancellations,
    SUM(CASE WHEN arr_del15 = 1 THEN 1 ELSE 0 END) AS delayed_flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                    AS delay_rate,
    ROUND(AVG(arr_delay_minutes), 1)                AS avg_arr_delay_minutes,
    ROUND(AVG(dep_delay_minutes), 1)                AS avg_dep_delay_minutes,
    SUM(carrier_delay)                              AS total_carrier_delay,
    SUM(weather_delay)                              AS total_weather_delay,
    SUM(nas_delay)                                  AS total_nas_delay,
    SUM(late_aircraft_delay)                        AS total_late_aircraft_delay
FROM flights
GROUP BY flight_date, origin, year, month, day_of_week;


-- ============================================================
-- VIEW 2: Monthly carrier-level performance
-- ============================================================
CREATE OR REPLACE VIEW v_monthly_carrier_performance AS
SELECT
    year,
    month,
    f.carrier_code,
    c.carrier_name,
    COUNT(*)                                                     AS total_flights,
    SUM(CASE WHEN f.cancelled = 1 THEN 1 ELSE 0 END)           AS cancellations,
    ROUND(100.0 * SUM(CASE WHEN f.cancelled = 1 THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                         AS cancellation_rate,
    SUM(CASE WHEN f.arr_del15 = 1 THEN 1 ELSE 0 END)           AS delayed_flights,
    ROUND(100.0 * (1 - AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END)), 2)
                                                                 AS on_time_pct,
    ROUND(AVG(f.arr_delay), 1)                                  AS avg_arr_delay,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.arr_delay), 1)
                                                                 AS median_arr_delay,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY f.arr_delay), 1)
                                                                 AS p95_arr_delay,
    SUM(f.arr_delay_minutes)                                    AS total_delay_minutes
FROM flights f
LEFT JOIN dim_carriers c USING (carrier_code)
GROUP BY year, month, f.carrier_code, c.carrier_name;


-- ============================================================
-- VIEW 3: Route reliability (min 100 flights)
-- ============================================================
CREATE OR REPLACE VIEW v_route_reliability AS
SELECT
    origin,
    dest,
    route,
    COUNT(*)                                                     AS total_flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                 AS delay_rate,
    ROUND(100.0 * (1 - AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END)), 2)
                                                                 AS on_time_pct,
    ROUND(AVG(arr_delay_minutes), 1)                            AS avg_delay_minutes,
    ROUND(AVG(distance), 0)                                     AS avg_distance,
    COUNT(DISTINCT carrier_code)                                AS num_carriers
FROM flights
WHERE cancelled = 0
GROUP BY origin, dest, route
HAVING COUNT(*) >= 100;
