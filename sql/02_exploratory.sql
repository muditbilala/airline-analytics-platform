-- ============================================================
-- EXPLORATORY ANALYSIS
-- Key business questions answered with SQL (DuckDB)
-- Data: Jan-May 2023 US domestic flights (~2.76M rows)
-- ============================================================


-- Q1: Overall KPI summary
--     Total flights, delay rate, cancellation rate, average delay
SELECT
    COUNT(*)                                                              AS total_flights,
    COUNT(*) FILTER (WHERE cancelled = 0)                                AS completed_flights,
    COUNT(*) FILTER (WHERE cancelled = 1)                                AS cancelled_flights,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cancelled = 1) / COUNT(*), 2)  AS cancel_rate_pct,
    COUNT(*) FILTER (WHERE arr_del15 = 1)                                AS delayed_flights,
    ROUND(100.0 * COUNT(*) FILTER (WHERE arr_del15 = 1)
          / NULLIF(COUNT(*) FILTER (WHERE cancelled = 0), 0), 2)        AS delay_rate_pct,
    ROUND(AVG(arr_delay) FILTER (WHERE cancelled = 0), 1)               AS avg_arr_delay_min,
    ROUND(AVG(dep_delay) FILTER (WHERE cancelled = 0), 1)               AS avg_dep_delay_min,
    ROUND(AVG(arr_delay_minutes) FILTER (WHERE cancelled = 0), 1)       AS avg_arr_delay_positive_min,
    ROUND(AVG(distance) FILTER (WHERE cancelled = 0), 0)                AS avg_distance_miles
FROM flights;


-- Q2: Delay by hour of day
--     Reveals how delays accumulate through the day
SELECT
    hour_of_day,
    COUNT(*)                                                              AS flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(arr_delay), 1)                                             AS avg_arr_delay,
    ROUND(AVG(dep_delay), 1)                                             AS avg_dep_delay
FROM flights
WHERE cancelled = 0 AND hour_of_day IS NOT NULL
GROUP BY hour_of_day
ORDER BY hour_of_day;


-- Q3: Delay by day of week
SELECT
    day_of_week,
    CASE day_of_week
        WHEN 1 THEN 'Monday'    WHEN 2 THEN 'Tuesday'  WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'  WHEN 5 THEN 'Friday'   WHEN 6 THEN 'Saturday'
        WHEN 7 THEN 'Sunday'
    END AS day_name,
    COUNT(*)                                                              AS flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(arr_delay), 1)                                             AS avg_arr_delay
FROM flights
WHERE cancelled = 0
GROUP BY day_of_week
ORDER BY day_of_week;


-- Q4: Delay by month (seasonal patterns across Jan-May 2023)
SELECT
    month,
    CASE month
        WHEN 1 THEN 'Jan' WHEN 2 THEN 'Feb' WHEN 3 THEN 'Mar'
        WHEN 4 THEN 'Apr' WHEN 5 THEN 'May' WHEN 6 THEN 'Jun'
        WHEN 7 THEN 'Jul' WHEN 8 THEN 'Aug' WHEN 9 THEN 'Sep'
        WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dec'
    END AS month_name,
    COUNT(*)                                                              AS flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(100.0 * AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS cancel_rate_pct,
    ROUND(AVG(arr_delay_minutes), 1)                                     AS avg_delay_min
FROM flights
GROUP BY month
ORDER BY month;


-- Q5: Top 10 busiest airports (by departures)
SELECT
    f.origin                                                              AS airport,
    a.airport_name,
    a.city,
    COUNT(*)                                                              AS departures,
    ROUND(100.0 * AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(f.arr_delay_minutes), 1)                                   AS avg_delay_min
FROM flights f
LEFT JOIN dim_airports a ON f.origin = a.iata_code
GROUP BY f.origin, a.airport_name, a.city
ORDER BY departures DESC
LIMIT 10;


-- Q6: Top 10 most delayed airports (by delay rate, min 5000 departures)
SELECT
    f.origin                                                              AS airport,
    a.airport_name,
    COUNT(*)                                                              AS departures,
    ROUND(100.0 * AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(f.arr_delay), 1)                                           AS avg_arr_delay,
    ROUND(AVG(f.dep_delay), 1)                                           AS avg_dep_delay
FROM flights f
LEFT JOIN dim_airports a ON f.origin = a.iata_code
WHERE f.cancelled = 0
GROUP BY f.origin, a.airport_name
HAVING COUNT(*) >= 5000
ORDER BY delay_rate_pct DESC
LIMIT 10;


-- Q7: Carrier ranking by on-time performance
SELECT
    f.carrier_code,
    c.carrier_name,
    COUNT(*)                                                              AS total_flights,
    ROUND(100.0 * (1 - AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END)), 2)
                                                                          AS on_time_pct,
    ROUND(AVG(f.arr_delay), 1)                                           AS avg_arr_delay,
    ROUND(100.0 * AVG(CASE WHEN f.cancelled = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS cancel_rate_pct,
    ROUND(AVG(f.arr_delay_minutes), 1)                                   AS avg_delay_when_late
FROM flights f
LEFT JOIN dim_carriers c USING (carrier_code)
GROUP BY f.carrier_code, c.carrier_name
HAVING COUNT(*) >= 1000
ORDER BY on_time_pct DESC;


-- Q8: Delay cause breakdown
--     Carrier vs Weather vs NAS vs Security vs Late Aircraft
SELECT
    cause,
    total_minutes,
    ROUND(100.0 * total_minutes / SUM(total_minutes) OVER (), 1) AS pct_of_total,
    flight_count
FROM (
    SELECT 'Carrier'       AS cause, SUM(carrier_delay)        AS total_minutes, COUNT(*) FILTER (WHERE carrier_delay > 0)        AS flight_count FROM flights WHERE arr_del15 = 1
    UNION ALL
    SELECT 'Weather',              SUM(weather_delay),                          COUNT(*) FILTER (WHERE weather_delay > 0)        FROM flights WHERE arr_del15 = 1
    UNION ALL
    SELECT 'NAS',                  SUM(nas_delay),                              COUNT(*) FILTER (WHERE nas_delay > 0)            FROM flights WHERE arr_del15 = 1
    UNION ALL
    SELECT 'Security',             SUM(security_delay),                         COUNT(*) FILTER (WHERE security_delay > 0)       FROM flights WHERE arr_del15 = 1
    UNION ALL
    SELECT 'Late Aircraft',        SUM(late_aircraft_delay),                    COUNT(*) FILTER (WHERE late_aircraft_delay > 0)  FROM flights WHERE arr_del15 = 1
) t
ORDER BY total_minutes DESC;


-- Q9: Top 20 busiest routes
SELECT
    route,
    origin,
    dest,
    COUNT(*)                                                              AS flights,
    COUNT(DISTINCT carrier_code)                                         AS num_carriers,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(arr_delay_minutes), 1)                                     AS avg_delay_min,
    ROUND(AVG(distance), 0)                                              AS avg_distance
FROM flights
WHERE cancelled = 0
GROUP BY route, origin, dest
ORDER BY flights DESC
LIMIT 20;


-- Q10: Weekend vs weekday delay comparison
SELECT
    CASE WHEN is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END          AS period,
    COUNT(*)                                                              AS flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(arr_delay), 1)                                             AS avg_arr_delay,
    ROUND(AVG(dep_delay), 1)                                             AS avg_dep_delay,
    ROUND(100.0 * AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS cancel_rate_pct
FROM flights
GROUP BY is_weekend
ORDER BY is_weekend;


-- Q11: Worst 20 routes by delay rate (min 500 flights for significance)
SELECT
    route,
    origin,
    dest,
    COUNT(*)                                                              AS flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                          AS delay_rate_pct,
    ROUND(AVG(arr_delay_minutes), 1)                                     AS avg_delay_min
FROM flights
WHERE cancelled = 0
GROUP BY route, origin, dest
HAVING COUNT(*) >= 500
ORDER BY delay_rate_pct DESC
LIMIT 20;


-- Q12: Primary delay cause distribution for delayed flights
SELECT
    primary_delay_cause,
    COUNT(*)                                                              AS flights,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)                  AS pct
FROM flights
WHERE primary_delay_cause IS NOT NULL
GROUP BY primary_delay_cause
ORDER BY flights DESC;
