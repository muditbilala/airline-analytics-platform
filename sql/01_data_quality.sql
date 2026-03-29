-- ============================================================
-- DATA QUALITY ASSESSMENT
-- Run after ETL to validate data integrity
-- Database: DuckDB
-- ============================================================

-- 1. Record counts by year-month (identify gaps or unexpected volumes)
SELECT
    year,
    month,
    COUNT(*)                      AS flight_count,
    COUNT(DISTINCT origin)        AS unique_origins,
    COUNT(DISTINCT dest)          AS unique_dests,
    COUNT(DISTINCT carrier_code)  AS unique_carriers,
    MIN(flight_date)              AS first_date,
    MAX(flight_date)              AS last_date
FROM flights
GROUP BY year, month
ORDER BY year, month;


-- 2. Null percentage for every key column
SELECT column_name, null_pct
FROM (
    SELECT 'arr_delay'           AS column_name, ROUND(100.0 * COUNT(*) FILTER (WHERE arr_delay IS NULL) / COUNT(*), 1) AS null_pct FROM flights
    UNION ALL
    SELECT 'dep_delay',          ROUND(100.0 * COUNT(*) FILTER (WHERE dep_delay IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'arr_delay_minutes',  ROUND(100.0 * COUNT(*) FILTER (WHERE arr_delay_minutes IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'dep_delay_minutes',  ROUND(100.0 * COUNT(*) FILTER (WHERE dep_delay_minutes IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'carrier_delay',      ROUND(100.0 * COUNT(*) FILTER (WHERE carrier_delay IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'weather_delay',      ROUND(100.0 * COUNT(*) FILTER (WHERE weather_delay IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'nas_delay',          ROUND(100.0 * COUNT(*) FILTER (WHERE nas_delay IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'cancelled',          ROUND(100.0 * COUNT(*) FILTER (WHERE cancelled IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'cancellation_code',  ROUND(100.0 * COUNT(*) FILTER (WHERE cancellation_code IS NULL) / COUNT(*), 1) FROM flights
    UNION ALL
    SELECT 'distance',           ROUND(100.0 * COUNT(*) FILTER (WHERE distance IS NULL) / COUNT(*), 1) FROM flights
) t
ORDER BY null_pct DESC;


-- 3. Arrival delay distribution (detect outliers and negatives)
SELECT
    MIN(arr_delay)                                                    AS min_delay,
    PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY arr_delay)          AS p01,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY arr_delay)          AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY arr_delay)          AS median,
    ROUND(AVG(arr_delay), 1)                                         AS mean,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY arr_delay)          AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY arr_delay)          AS p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY arr_delay)          AS p99,
    MAX(arr_delay)                                                    AS max_delay,
    COUNT(*) FILTER (WHERE arr_delay < 0)                            AS early_arrivals,
    COUNT(*) FILTER (WHERE arr_delay >= 0 AND arr_delay < 15)        AS on_time,
    COUNT(*) FILTER (WHERE arr_delay >= 15)                          AS delayed
FROM flights
WHERE arr_delay IS NOT NULL;


-- 4. Cancellation code distribution
SELECT
    cancellation_code,
    CASE cancellation_code
        WHEN 'A' THEN 'Carrier'
        WHEN 'B' THEN 'Weather'
        WHEN 'C' THEN 'NAS (National Aviation System)'
        WHEN 'D' THEN 'Security'
        ELSE 'Unknown'
    END AS reason,
    COUNT(*)                                                          AS count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)               AS pct
FROM flights
WHERE cancelled = 1
GROUP BY cancellation_code
ORDER BY count DESC;


-- 5. Check for orphan airport codes (origins with no matching airport in dim_airports)
SELECT
    f.origin AS orphan_airport,
    COUNT(*) AS flight_count
FROM flights f
LEFT JOIN dim_airports a ON f.origin = a.iata_code
WHERE a.iata_code IS NULL
GROUP BY f.origin
ORDER BY flight_count DESC
LIMIT 20;


-- 6. Flights per day distribution (spot anomalous low/high-volume days)
WITH daily AS (
    SELECT
        flight_date,
        COUNT(*) AS daily_flights
    FROM flights
    GROUP BY flight_date
)
SELECT
    MIN(daily_flights)                                                AS min_daily,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY daily_flights)      AS p25_daily,
    ROUND(AVG(daily_flights), 0)                                     AS avg_daily,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY daily_flights)      AS median_daily,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY daily_flights)      AS p75_daily,
    MAX(daily_flights)                                                AS max_daily,
    COUNT(*)                                                          AS total_days
FROM daily;
