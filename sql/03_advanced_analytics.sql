-- ====================================================================
-- ADVANCED ANALYTICS — Interview-Killer SQL Queries
-- Window functions, recursive CTEs, advanced aggregations, pivots
-- Database: DuckDB  |  Data: Jan-May 2023 US domestic flights
-- ====================================================================
-- This file demonstrates senior-level SQL proficiency through
-- production-grade analytical queries. Each query solves a real
-- business problem in airline operations and is annotated with
-- the reasoning behind the approach.
-- ====================================================================


-- ====================================================================
-- Q1: TOP 5 AIRLINES RANKED BY ON-TIME PERFORMANCE USING RANK()
-- ====================================================================
-- Business value: Operations teams need a single leaderboard that
-- accounts for ties. RANK() leaves gaps after ties (1,2,2,4) while
-- DENSE_RANK() does not (1,2,2,3). We show both so stakeholders
-- can choose the convention that fits their reporting standard.
-- ROW_NUMBER() is added for deterministic row ordering (no ties).
-- ====================================================================

WITH carrier_performance AS (
    SELECT
        f.carrier_code,
        c.carrier_name,
        COUNT(*)                                                                AS total_flights,
        SUM(CASE WHEN f.arr_del15 = 0 THEN 1 ELSE 0 END)                     AS on_time_flights,
        ROUND(100.0 * SUM(CASE WHEN f.arr_del15 = 0 THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                                    AS on_time_pct,
        ROUND(AVG(f.arr_delay), 2)                                             AS avg_arr_delay_min,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY f.arr_delay), 1)   AS median_arr_delay,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY f.arr_delay), 1)   AS p95_arr_delay
    FROM flights f
    LEFT JOIN dim_carriers c USING (carrier_code)
    WHERE f.cancelled = 0
    GROUP BY f.carrier_code, c.carrier_name
    HAVING COUNT(*) >= 1000                -- filter out tiny regional samples
)
SELECT
    carrier_code,
    carrier_name,
    total_flights,
    on_time_pct,
    avg_arr_delay_min,
    median_arr_delay,
    p95_arr_delay,
    RANK()       OVER (ORDER BY on_time_pct DESC)                              AS rank_on_time,
    DENSE_RANK() OVER (ORDER BY on_time_pct DESC)                              AS dense_rank_on_time,
    ROW_NUMBER() OVER (ORDER BY on_time_pct DESC, total_flights DESC)          AS row_num
FROM carrier_performance
ORDER BY rank_on_time
LIMIT 5;


-- ====================================================================
-- Q2: MONTH-OVER-MONTH DELAY TREND WITH LAG() SHOWING CHANGE
-- ====================================================================
-- Business value: Executives track delay KPIs monthly. LAG() gives
-- the previous month's value so we can compute both the absolute
-- change (percentage-point delta) and the relative change (% growth).
-- LEAD() previews next month for forward-looking commentary.
-- ====================================================================

WITH monthly_kpi AS (
    SELECT
        year,
        month,
        COUNT(*)                                                                AS flights,
        ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2) AS delay_rate_pct,
        ROUND(AVG(arr_delay), 2)                                               AS avg_arr_delay,
        ROUND(AVG(dep_delay), 2)                                               AS avg_dep_delay,
        ROUND(100.0 * AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END), 2) AS cancel_rate_pct
    FROM flights
    GROUP BY year, month
)
SELECT
    year,
    month,
    flights,
    delay_rate_pct,

    -- Previous and next month values
    LAG(delay_rate_pct, 1)  OVER (ORDER BY year, month)                        AS prev_month_delay_rate,
    LEAD(delay_rate_pct, 1) OVER (ORDER BY year, month)                        AS next_month_delay_rate,

    -- Absolute change in percentage points
    ROUND(
        delay_rate_pct - LAG(delay_rate_pct, 1) OVER (ORDER BY year, month), 2
    )                                                                           AS mom_change_pp,

    -- Relative change (% growth over previous month's rate)
    ROUND(
        100.0 * (delay_rate_pct - LAG(delay_rate_pct, 1) OVER (ORDER BY year, month))
        / NULLIF(LAG(delay_rate_pct, 1) OVER (ORDER BY year, month), 0), 2
    )                                                                           AS mom_change_pct,

    avg_arr_delay,
    LAG(avg_arr_delay, 1) OVER (ORDER BY year, month)                          AS prev_avg_arr_delay,
    cancel_rate_pct,
    LAG(cancel_rate_pct, 1) OVER (ORDER BY year, month)                        AS prev_cancel_rate
FROM monthly_kpi
ORDER BY year, month;


-- ====================================================================
-- Q3: AIRPORT CONGESTION SCORING WITH NTILE AND PERCENT_RANK
-- ====================================================================
-- Business value: Classify airports into congestion tiers so the
-- network planning team can identify bottleneck airports. NTILE(5)
-- creates five equal-sized buckets (quintiles). PERCENT_RANK gives
-- a 0-1 continuous score for finer-grained ranking. The composite
-- congestion_score blends delay rate, volume, and average delay.
-- ====================================================================

WITH airport_metrics AS (
    SELECT
        f.origin                                                                AS airport,
        a.airport_name,
        a.city,
        COUNT(*)                                                                AS departures,
        ROUND(100.0 * AVG(CASE WHEN f.dep_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS dep_delay_rate_pct,
        ROUND(AVG(f.dep_delay), 2)                                             AS avg_dep_delay,
        ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY f.dep_delay), 1)   AS p90_dep_delay,
        ROUND(100.0 * AVG(CASE WHEN f.cancelled = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS cancel_rate_pct
    FROM flights f
    LEFT JOIN dim_airports a ON f.origin = a.iata_code
    GROUP BY f.origin, a.airport_name, a.city
    HAVING COUNT(*) >= 500                 -- minimum sample for statistical relevance
),
scored AS (
    SELECT
        *,
        -- Composite congestion score: weighted blend of normalized metrics
        ROUND(
            0.40 * PERCENT_RANK() OVER (ORDER BY dep_delay_rate_pct)
          + 0.30 * PERCENT_RANK() OVER (ORDER BY avg_dep_delay)
          + 0.20 * PERCENT_RANK() OVER (ORDER BY p90_dep_delay)
          + 0.10 * PERCENT_RANK() OVER (ORDER BY cancel_rate_pct)
        , 4)                                                                    AS congestion_score,

        NTILE(5) OVER (ORDER BY dep_delay_rate_pct)                            AS delay_quintile,

        ROUND(PERCENT_RANK() OVER (ORDER BY dep_delay_rate_pct), 4)           AS delay_percentile_rank
    FROM airport_metrics
)
SELECT
    airport,
    airport_name,
    city,
    departures,
    dep_delay_rate_pct,
    avg_dep_delay,
    p90_dep_delay,
    cancel_rate_pct,
    congestion_score,
    delay_quintile,
    CASE delay_quintile
        WHEN 1 THEN 'Excellent'
        WHEN 2 THEN 'Good'
        WHEN 3 THEN 'Average'
        WHEN 4 THEN 'Congested'
        WHEN 5 THEN 'Severely Congested'
    END                                                                         AS congestion_tier,
    delay_percentile_rank
FROM scored
ORDER BY congestion_score DESC;


-- ====================================================================
-- Q4: DELAY CASCADE ANALYSIS — LATE AIRCRAFT DELAY PROPAGATION
-- ====================================================================
-- Business value: Late aircraft delays are the #1 controllable
-- source of cascading disruption. This query traces how an
-- incoming late aircraft affects the outbound flight, measuring
-- whether delays compound or recover. We use window functions to
-- track sequential flights at the same airport within the day to
-- quantify the ripple effect.
-- ====================================================================

WITH late_aircraft_flights AS (
    SELECT
        carrier_code,
        origin,
        flight_date,
        hour_of_day,
        dep_delay,
        arr_delay,
        late_aircraft_delay,
        carrier_delay,
        weather_delay,
        nas_delay,
        -- How much delay grew (positive = worsened, negative = recovered)
        arr_delay - dep_delay                                                   AS in_air_delta,
        -- What fraction of total delay came from late aircraft
        ROUND(100.0 * late_aircraft_delay
              / NULLIF(arr_delay_minutes, 0), 1)                               AS late_aircraft_pct_of_delay
    FROM flights
    WHERE cancelled = 0
      AND late_aircraft_delay > 0
      AND dep_delay IS NOT NULL
      AND arr_delay IS NOT NULL
),
cascade_summary AS (
    SELECT
        carrier_code,
        COUNT(*)                                                                AS affected_flights,
        ROUND(AVG(late_aircraft_delay), 1)                                     AS avg_late_aircraft_min,
        ROUND(AVG(dep_delay), 1)                                               AS avg_dep_delay,
        ROUND(AVG(arr_delay), 1)                                               AS avg_arr_delay,
        ROUND(AVG(in_air_delta), 1)                                            AS avg_in_air_delta,
        ROUND(AVG(late_aircraft_pct_of_delay), 1)                              AS avg_late_aircraft_pct,
        SUM(CASE WHEN in_air_delta > 0 THEN 1 ELSE 0 END)                     AS worsened_count,
        SUM(CASE WHEN in_air_delta < 0 THEN 1 ELSE 0 END)                     AS recovered_count,
        SUM(CASE WHEN in_air_delta = 0 THEN 1 ELSE 0 END)                     AS unchanged_count,
        -- Correlation proxy: Pearson-style covariance between late_aircraft and arr_delay
        ROUND(CORR(late_aircraft_delay, arr_delay), 4)                         AS corr_late_aircraft_arr
    FROM late_aircraft_flights
    GROUP BY carrier_code
)
SELECT
    cs.carrier_code,
    c.carrier_name,
    cs.affected_flights,
    cs.avg_late_aircraft_min,
    cs.avg_dep_delay,
    cs.avg_arr_delay,
    cs.avg_in_air_delta,
    cs.avg_late_aircraft_pct,
    cs.worsened_count,
    cs.recovered_count,
    ROUND(100.0 * cs.worsened_count / cs.affected_flights, 1)                  AS pct_worsened,
    cs.corr_late_aircraft_arr,
    RANK() OVER (ORDER BY cs.avg_in_air_delta DESC)                            AS cascade_severity_rank
FROM cascade_summary cs
LEFT JOIN dim_carriers c USING (carrier_code)
ORDER BY cascade_severity_rank;


-- ====================================================================
-- Q5: ROUTE-LEVEL DELAY DECOMPOSITION — CARRIER vs WEATHER vs NAS
-- ====================================================================
-- Business value: For the busiest routes, break down what causes
-- delays. This lets operations assign accountability: carrier-caused
-- delays are controllable, weather is not, and NAS delays suggest
-- airspace/infrastructure issues that need FAA coordination.
-- The proportional split uses FILTER aggregation for clarity.
-- ====================================================================

WITH top_routes AS (
    SELECT route
    FROM flights
    WHERE cancelled = 0
    GROUP BY route
    ORDER BY COUNT(*) DESC
    LIMIT 50
),
route_delays AS (
    SELECT
        f.route,
        f.origin,
        f.dest,
        COUNT(*)                                                                AS total_flights,
        SUM(CASE WHEN f.arr_del15 = 1 THEN 1 ELSE 0 END)                     AS delayed_flights,
        ROUND(100.0 * AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS delay_rate_pct,
        -- Average minutes attributed to each cause (across ALL flights, not just delayed)
        ROUND(AVG(f.carrier_delay), 2)                                         AS avg_carrier_delay,
        ROUND(AVG(f.weather_delay), 2)                                         AS avg_weather_delay,
        ROUND(AVG(f.nas_delay), 2)                                             AS avg_nas_delay,
        ROUND(AVG(f.security_delay), 2)                                        AS avg_security_delay,
        ROUND(AVG(f.late_aircraft_delay), 2)                                   AS avg_late_aircraft_delay,

        -- Total delay minutes by cause (for delayed flights only)
        SUM(f.carrier_delay)                                                    AS total_carrier_min,
        SUM(f.weather_delay)                                                    AS total_weather_min,
        SUM(f.nas_delay)                                                        AS total_nas_min,
        SUM(f.security_delay)                                                   AS total_security_min,
        SUM(f.late_aircraft_delay)                                              AS total_late_aircraft_min
    FROM flights f
    JOIN top_routes tr ON f.route = tr.route
    WHERE f.cancelled = 0
    GROUP BY f.route, f.origin, f.dest
)
SELECT
    route,
    origin,
    dest,
    total_flights,
    delayed_flights,
    delay_rate_pct,
    avg_carrier_delay,
    avg_weather_delay,
    avg_nas_delay,
    avg_late_aircraft_delay,

    -- Proportional split of delay minutes by cause
    ROUND(100.0 * total_carrier_min
          / NULLIF(total_carrier_min + total_weather_min + total_nas_min
                   + total_security_min + total_late_aircraft_min, 0), 1)       AS pct_carrier,
    ROUND(100.0 * total_weather_min
          / NULLIF(total_carrier_min + total_weather_min + total_nas_min
                   + total_security_min + total_late_aircraft_min, 0), 1)       AS pct_weather,
    ROUND(100.0 * total_nas_min
          / NULLIF(total_carrier_min + total_weather_min + total_nas_min
                   + total_security_min + total_late_aircraft_min, 0), 1)       AS pct_nas,
    ROUND(100.0 * total_late_aircraft_min
          / NULLIF(total_carrier_min + total_weather_min + total_nas_min
                   + total_security_min + total_late_aircraft_min, 0), 1)       AS pct_late_aircraft,

    -- Dominant delay cause label
    CASE
        WHEN total_carrier_min >= GREATEST(total_weather_min, total_nas_min, total_late_aircraft_min)
            THEN 'Carrier'
        WHEN total_weather_min >= GREATEST(total_carrier_min, total_nas_min, total_late_aircraft_min)
            THEN 'Weather'
        WHEN total_nas_min >= GREATEST(total_carrier_min, total_weather_min, total_late_aircraft_min)
            THEN 'NAS'
        ELSE 'Late Aircraft'
    END                                                                         AS dominant_cause
FROM route_delays
ORDER BY delay_rate_pct DESC;


-- ====================================================================
-- Q6: HUB AIRPORT EFFICIENCY COMPARISON
-- ====================================================================
-- Business value: Hub airports handle connecting traffic and are
-- critical to network performance. This query identifies the top 30
-- airports by volume (hubs), ranks them against each other on delay
-- and throughput metrics, and compares hub vs non-hub averages.
-- Useful for operations reviews and infrastructure investment cases.
-- ====================================================================

WITH airport_volume AS (
    SELECT
        origin                                                                  AS airport,
        COUNT(*)                                                                AS total_departures
    FROM flights
    GROUP BY origin
),
hub_threshold AS (
    -- The 30th-largest airport's departure count becomes the cutoff
    SELECT MIN(total_departures) AS min_hub_departures
    FROM (
        SELECT total_departures
        FROM airport_volume
        ORDER BY total_departures DESC
        LIMIT 30
    )
),
hub_airports AS (
    SELECT
        f.origin                                                                AS airport,
        a.airport_name,
        a.city,
        COUNT(*)                                                                AS departures,
        ROUND(100.0 * AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS delay_rate_pct,
        ROUND(AVG(f.arr_delay), 2)                                             AS avg_arr_delay,
        ROUND(AVG(f.dep_delay), 2)                                             AS avg_dep_delay,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY f.dep_delay), 1)   AS p95_dep_delay,
        ROUND(100.0 * AVG(CASE WHEN f.cancelled = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS cancel_rate_pct,
        COUNT(DISTINCT f.dest)                                                  AS destinations_served,
        COUNT(DISTINCT f.carrier_code)                                          AS carriers_operating,
        ROUND(AVG(f.distance), 0)                                              AS avg_route_distance
    FROM flights f
    LEFT JOIN dim_airports a ON f.origin = a.iata_code
    GROUP BY f.origin, a.airport_name, a.city
    HAVING COUNT(*) >= (SELECT min_hub_departures FROM hub_threshold)
)
SELECT
    airport,
    airport_name,
    city,
    departures,
    delay_rate_pct,
    avg_arr_delay,
    avg_dep_delay,
    p95_dep_delay,
    cancel_rate_pct,
    destinations_served,
    carriers_operating,
    avg_route_distance,
    RANK()       OVER (ORDER BY delay_rate_pct ASC)                            AS efficiency_rank,
    DENSE_RANK() OVER (ORDER BY departures DESC)                               AS volume_rank,
    NTILE(3)     OVER (ORDER BY delay_rate_pct ASC)                            AS efficiency_tier
    -- Tier 1 = best third, Tier 3 = worst third
FROM hub_airports
ORDER BY efficiency_rank;


-- ====================================================================
-- Q7: HOUR x DAY-OF-WEEK DELAY HEATMAP — PIVOTED DATA
-- ====================================================================
-- Business value: This feeds directly into a heatmap visualization
-- showing when delays peak. The PIVOT syntax transforms rows into
-- columns so each day-of-week becomes its own column. Scheduling
-- teams use this to avoid booking tight turnarounds during
-- high-delay windows (e.g., Friday evenings).
-- ====================================================================

-- 7a: Raw heatmap data (long format, works with any viz tool)
SELECT
    hour_of_day,
    day_of_week,
    CASE day_of_week
        WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed'
        WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat'
        WHEN 7 THEN 'Sun'
    END                                                                         AS day_name,
    COUNT(*)                                                                    AS flights,
    ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)     AS delay_rate_pct,
    ROUND(AVG(arr_delay), 1)                                                   AS avg_arr_delay
FROM flights
WHERE cancelled = 0
  AND hour_of_day IS NOT NULL
GROUP BY hour_of_day, day_of_week
ORDER BY hour_of_day, day_of_week;

-- 7b: Pivoted format (wide format, one column per day)
--     DuckDB supports the PIVOT statement natively
PIVOT (
    SELECT
        hour_of_day,
        CASE day_of_week
            WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue' WHEN 3 THEN 'Wed'
            WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' WHEN 6 THEN 'Sat'
            WHEN 7 THEN 'Sun'
        END AS day_name,
        ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2) AS delay_rate
    FROM flights
    WHERE cancelled = 0 AND hour_of_day IS NOT NULL
    GROUP BY hour_of_day, day_of_week
)
ON day_name
USING FIRST(delay_rate)
ORDER BY hour_of_day;


-- ====================================================================
-- Q8: CARRIER MARKET SHARE vs DELAY RATE CORRELATION
-- ====================================================================
-- Business value: Tests the hypothesis "bigger airlines have worse
-- delays." Market share is computed as % of total flights. We rank
-- carriers on both dimensions and compute a Spearman-like rank
-- difference to quantify the relationship. This drives competitive
-- benchmarking and investor presentations.
-- ====================================================================

WITH carrier_stats AS (
    SELECT
        f.carrier_code,
        c.carrier_name,
        COUNT(*)                                                                AS total_flights,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)                    AS market_share_pct,
        ROUND(100.0 * AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS delay_rate_pct,
        ROUND(AVG(f.arr_delay), 2)                                             AS avg_arr_delay,
        COUNT(DISTINCT f.route)                                                 AS routes_served,
        COUNT(DISTINCT f.origin)                                                AS airports_served
    FROM flights f
    LEFT JOIN dim_carriers c USING (carrier_code)
    WHERE f.cancelled = 0
    GROUP BY f.carrier_code, c.carrier_name
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY market_share_pct DESC)                           AS market_rank,
        RANK() OVER (ORDER BY delay_rate_pct ASC)                              AS reliability_rank,
        -- Rank difference: positive = more reliable than size would predict
        RANK() OVER (ORDER BY market_share_pct DESC)
          - RANK() OVER (ORDER BY delay_rate_pct ASC)                          AS rank_gap
    FROM carrier_stats
)
SELECT
    carrier_code,
    carrier_name,
    total_flights,
    market_share_pct,
    delay_rate_pct,
    avg_arr_delay,
    routes_served,
    airports_served,
    market_rank,
    reliability_rank,
    rank_gap,
    CASE
        WHEN rank_gap > 2  THEN 'Underperformer (big but unreliable)'
        WHEN rank_gap < -2 THEN 'Overperformer (big and reliable)'
        ELSE 'In line with size'
    END                                                                         AS performance_vs_size
FROM ranked
ORDER BY market_share_pct DESC;


-- ====================================================================
-- Q9: CANCELLATION PATTERN ANALYSIS BY SEASON AND CAUSE
-- ====================================================================
-- Business value: Understanding seasonal cancellation drivers lets
-- the planning team pre-position resources (e.g., de-icing crews in
-- winter, rebooking agents during weather season). We join to
-- dim_calendar for season and break down by cancellation code:
--   A = Carrier, B = Weather, C = NAS, D = Security
-- ====================================================================

WITH cancellation_detail AS (
    SELECT
        cal.season,
        f.month,
        f.cancellation_code,
        CASE f.cancellation_code
            WHEN 'A' THEN 'Carrier'
            WHEN 'B' THEN 'Weather'
            WHEN 'C' THEN 'NAS (National Airspace System)'
            WHEN 'D' THEN 'Security'
            ELSE 'Unknown'
        END                                                                     AS cancel_reason,
        COUNT(*)                                                                AS cancellations
    FROM flights f
    LEFT JOIN dim_calendar cal ON f.flight_date = cal.flight_date
    WHERE f.cancelled = 1
    GROUP BY cal.season, f.month, f.cancellation_code
),
season_totals AS (
    SELECT
        season,
        SUM(cancellations)                                                      AS season_total_cancels
    FROM cancellation_detail
    GROUP BY season
)
SELECT
    cd.season,
    cd.cancel_reason,
    cd.cancellation_code,
    SUM(cd.cancellations)                                                       AS cancellations,
    st.season_total_cancels,
    ROUND(100.0 * SUM(cd.cancellations) / st.season_total_cancels, 1)         AS pct_of_season,
    -- Rank causes within each season
    RANK() OVER (
        PARTITION BY cd.season
        ORDER BY SUM(cd.cancellations) DESC
    )                                                                           AS cause_rank_in_season
FROM cancellation_detail cd
JOIN season_totals st ON cd.season = st.season
GROUP BY cd.season, cd.cancel_reason, cd.cancellation_code, st.season_total_cancels
ORDER BY cd.season, cause_rank_in_season;


-- ====================================================================
-- Q10: ROLLING 7-DAY DELAY AVERAGE WITH WINDOW FRAMES
-- ====================================================================
-- Business value: Daily delay rates are noisy. A rolling 7-day
-- average smooths out day-to-day variance and reveals underlying
-- trends. The ROWS BETWEEN 6 PRECEDING AND CURRENT ROW frame gives
-- a trailing 7-day window. We also compute a centered window and
-- a 14-day window for comparison.
-- ====================================================================

WITH daily_stats AS (
    SELECT
        flight_date,
        COUNT(*)                                                                AS flights,
        ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2) AS delay_rate_pct,
        ROUND(AVG(arr_delay), 2)                                               AS avg_arr_delay,
        SUM(arr_delay_minutes)                                                  AS total_delay_minutes
    FROM flights
    WHERE cancelled = 0
    GROUP BY flight_date
)
SELECT
    flight_date,
    flights,
    delay_rate_pct,
    avg_arr_delay,

    -- Trailing 7-day rolling average
    ROUND(AVG(delay_rate_pct) OVER (
        ORDER BY flight_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2)                                                                       AS rolling_7d_delay_rate,

    -- Centered 7-day rolling average (3 before, current, 3 after)
    ROUND(AVG(delay_rate_pct) OVER (
        ORDER BY flight_date
        ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING
    ), 2)                                                                       AS centered_7d_delay_rate,

    -- Trailing 14-day rolling average for longer-term trend
    ROUND(AVG(delay_rate_pct) OVER (
        ORDER BY flight_date
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ), 2)                                                                       AS rolling_14d_delay_rate,

    -- Rolling sum of delay minutes (operational cost metric)
    SUM(total_delay_minutes) OVER (
        ORDER BY flight_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                                                           AS rolling_7d_total_delay_min,

    -- Rolling min and max (volatility indicator)
    MIN(delay_rate_pct) OVER (
        ORDER BY flight_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                                                           AS rolling_7d_min,
    MAX(delay_rate_pct) OVER (
        ORDER BY flight_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                                                           AS rolling_7d_max

FROM daily_stats
ORDER BY flight_date;


-- ====================================================================
-- Q11: YEAR-OVER-YEAR SAME-MONTH COMPARISON
-- ====================================================================
-- Business value: YoY comparison is the gold standard for seasonal
-- businesses. Even with only Jan-May 2023 data, this query pattern
-- is production-ready for multi-year datasets. It self-joins on
-- month and uses LAG with PARTITION BY month to pull prior-year
-- values. The query pattern generalizes to any time granularity.
-- ====================================================================

-- Note: With single-year data, prior_year columns will be NULL.
-- The query structure is designed to work as-is when 2024+ data arrives.

WITH monthly_metrics AS (
    SELECT
        year,
        month,
        COUNT(*)                                                                AS flights,
        ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2) AS delay_rate_pct,
        ROUND(AVG(arr_delay), 2)                                               AS avg_arr_delay,
        ROUND(100.0 * AVG(CASE WHEN cancelled = 1 THEN 1.0 ELSE 0.0 END), 2) AS cancel_rate_pct,
        SUM(arr_delay_minutes)                                                  AS total_delay_minutes
    FROM flights
    GROUP BY year, month
),
yoy AS (
    SELECT
        year,
        month,
        flights,
        delay_rate_pct,
        avg_arr_delay,
        cancel_rate_pct,
        total_delay_minutes,

        -- Prior year same month
        LAG(flights, 12)           OVER (ORDER BY year * 12 + month)           AS py_flights,
        LAG(delay_rate_pct, 12)    OVER (ORDER BY year * 12 + month)           AS py_delay_rate_pct,
        LAG(avg_arr_delay, 12)     OVER (ORDER BY year * 12 + month)           AS py_avg_arr_delay,
        LAG(cancel_rate_pct, 12)   OVER (ORDER BY year * 12 + month)           AS py_cancel_rate_pct
    FROM monthly_metrics
)
SELECT
    year,
    month,
    flights,
    delay_rate_pct,

    py_flights,
    py_delay_rate_pct,

    -- YoY changes
    ROUND(delay_rate_pct - COALESCE(py_delay_rate_pct, 0), 2)                 AS yoy_delay_change_pp,
    ROUND(100.0 * (flights - COALESCE(py_flights, 0))
          / NULLIF(py_flights, 0), 2)                                          AS yoy_flights_change_pct,
    ROUND(avg_arr_delay - COALESCE(py_avg_arr_delay, 0), 2)                   AS yoy_avg_delay_change,

    -- Flag improvement or degradation
    CASE
        WHEN py_delay_rate_pct IS NULL THEN 'No prior year'
        WHEN delay_rate_pct < py_delay_rate_pct THEN 'Improved'
        WHEN delay_rate_pct > py_delay_rate_pct THEN 'Degraded'
        ELSE 'Unchanged'
    END                                                                         AS yoy_trend
FROM yoy
ORDER BY year, month;


-- ====================================================================
-- Q12: TOP 10 WORST ROUTES BY DELAY SEVERITY — COMPOSITE SCORING
-- ====================================================================
-- Business value: A single "delay rate" metric misses severity.
-- A route with 30% delay rate but 20-min average delays is better
-- than one with 25% rate but 90-min average. This composite score
-- weights multiple factors:
--   - Delay frequency (rate)         : 30% weight
--   - Delay magnitude (avg minutes)  : 25% weight
--   - Tail risk (P95 delay)          : 20% weight
--   - Cancellation rate              : 15% weight
--   - Delay volatility (stddev)      : 10% weight
-- All metrics are normalized to 0-1 via PERCENT_RANK before weighting.
-- ====================================================================

WITH route_metrics AS (
    SELECT
        f.route,
        f.origin,
        f.dest,
        oa.city                                                                 AS origin_city,
        da.city                                                                 AS dest_city,
        COUNT(*)                                                                AS total_flights,
        ROUND(100.0 * AVG(CASE WHEN f.arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2)
                                                                                AS delay_rate_pct,
        ROUND(AVG(f.arr_delay_minutes), 2)                                     AS avg_delay_when_late,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY f.arr_delay), 1)   AS p95_arr_delay,
        ROUND(STDDEV(f.arr_delay), 2)                                          AS stddev_arr_delay,
        ROUND(100.0 * SUM(CASE WHEN f.cancelled = 1 THEN 1 ELSE 0 END)
              / COUNT(*), 2)                                                    AS cancel_rate_pct
    FROM flights f
    LEFT JOIN dim_airports oa ON f.origin = oa.iata_code
    LEFT JOIN dim_airports da ON f.dest = da.iata_code
    GROUP BY f.route, f.origin, f.dest, oa.city, da.city
    HAVING COUNT(*) >= 200                 -- minimum flights for statistical validity
),
normalized AS (
    SELECT
        *,
        PERCENT_RANK() OVER (ORDER BY delay_rate_pct)                          AS norm_delay_rate,
        PERCENT_RANK() OVER (ORDER BY avg_delay_when_late)                     AS norm_avg_delay,
        PERCENT_RANK() OVER (ORDER BY p95_arr_delay)                           AS norm_p95,
        PERCENT_RANK() OVER (ORDER BY cancel_rate_pct)                         AS norm_cancel,
        PERCENT_RANK() OVER (ORDER BY stddev_arr_delay)                        AS norm_volatility
    FROM route_metrics
),
scored AS (
    SELECT
        *,
        ROUND(
            0.30 * norm_delay_rate
          + 0.25 * norm_avg_delay
          + 0.20 * norm_p95
          + 0.15 * norm_cancel
          + 0.10 * norm_volatility
        , 4)                                                                    AS severity_score,
        ROW_NUMBER() OVER (
            ORDER BY (0.30 * norm_delay_rate
                    + 0.25 * norm_avg_delay
                    + 0.20 * norm_p95
                    + 0.15 * norm_cancel
                    + 0.10 * norm_volatility) DESC
        )                                                                       AS severity_rank
    FROM normalized
)
SELECT
    severity_rank,
    route,
    origin_city || ' -> ' || dest_city                                          AS city_pair,
    total_flights,
    delay_rate_pct,
    avg_delay_when_late,
    p95_arr_delay,
    stddev_arr_delay,
    cancel_rate_pct,
    severity_score
FROM scored
WHERE severity_rank <= 10
ORDER BY severity_rank;


-- ====================================================================
-- BONUS Q13: RECURSIVE CTE — BUILDING A FLIGHT CONNECTION CHAIN
-- ====================================================================
-- Business value: Demonstrates recursive CTE capability. Given a
-- starting airport and date, trace possible 1-stop and 2-stop
-- connections. Useful for rebooking engines and network analysis.
-- Note: This is a pattern demonstration; in production you would
-- parameterize the origin, date, and time constraints.
-- ====================================================================

WITH RECURSIVE connections AS (
    -- Base case: direct flights from ATL on a sample date
    SELECT
        origin                                                                  AS start_airport,
        dest                                                                    AS current_airport,
        route                                                                   AS path,
        1                                                                       AS stops,
        arr_time                                                                AS last_arrival,
        arr_delay                                                               AS total_delay
    FROM flights
    WHERE origin = 'ATL'
      AND flight_date = '2023-03-15'
      AND cancelled = 0
      AND arr_time IS NOT NULL

    UNION ALL

    -- Recursive step: extend with a connecting flight
    SELECT
        c.start_airport,
        f.dest                                                                  AS current_airport,
        c.path || ' -> ' || f.dest                                             AS path,
        c.stops + 1                                                             AS stops,
        f.arr_time                                                              AS last_arrival,
        c.total_delay + COALESCE(f.arr_delay, 0)                               AS total_delay
    FROM connections c
    JOIN flights f
        ON f.origin = c.current_airport
       AND f.flight_date = '2023-03-15'
       AND f.cancelled = 0
       AND f.dep_time > c.last_arrival + 60    -- at least 60-min connection
       AND f.arr_time IS NOT NULL
    WHERE c.stops < 2                          -- limit to 2-stop itineraries
)
SELECT
    start_airport,
    current_airport                                                             AS final_dest,
    path,
    stops,
    total_delay,
    ROW_NUMBER() OVER (
        PARTITION BY current_airport
        ORDER BY total_delay ASC
    )                                                                           AS route_rank
FROM connections
QUALIFY route_rank <= 3                        -- top 3 best options per destination
ORDER BY final_dest, route_rank;


-- ====================================================================
-- BONUS Q14: CUMULATIVE DISTRIBUTION — DELAY SEVERITY BUCKETS
-- ====================================================================
-- Business value: Shows what percentage of flights fall at or below
-- each delay threshold. This is the data behind "X% of our flights
-- arrive within Y minutes of schedule" — a key customer promise.
-- Uses CUME_DIST() and SUM() OVER() for running totals.
-- ====================================================================

WITH delay_buckets AS (
    SELECT
        CASE
            WHEN arr_delay <= -15  THEN '01: >15min Early'
            WHEN arr_delay <= 0    THEN '02: On Time / Early'
            WHEN arr_delay <= 15   THEN '03: 1-15min Late'
            WHEN arr_delay <= 30   THEN '04: 16-30min Late'
            WHEN arr_delay <= 60   THEN '05: 31-60min Late'
            WHEN arr_delay <= 120  THEN '06: 61-120min Late'
            WHEN arr_delay <= 240  THEN '07: 121-240min Late'
            ELSE                        '08: 240+min Late'
        END                                                                     AS delay_bucket,
        COUNT(*)                                                                AS flights
    FROM flights
    WHERE cancelled = 0 AND arr_delay IS NOT NULL
    GROUP BY delay_bucket
)
SELECT
    delay_bucket,
    flights,
    ROUND(100.0 * flights / SUM(flights) OVER (), 2)                          AS pct_of_total,
    ROUND(100.0 * SUM(flights) OVER (ORDER BY delay_bucket
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / SUM(flights) OVER (), 2)                                              AS cumulative_pct
FROM delay_buckets
ORDER BY delay_bucket;


-- ====================================================================
-- BONUS Q15: CARRIER PERFORMANCE MOMENTUM — IMPROVING OR DECLINING?
-- ====================================================================
-- Business value: Identifies which carriers are getting better or
-- worse over time using linear regression on monthly delay rates.
-- A negative slope means improvement; positive means degradation.
-- DuckDB's REGR_SLOPE() computes OLS regression in a single call.
-- ====================================================================

WITH carrier_monthly AS (
    SELECT
        carrier_code,
        month,
        COUNT(*)                                                                AS flights,
        ROUND(100.0 * AVG(CASE WHEN arr_del15 = 1 THEN 1.0 ELSE 0.0 END), 2) AS delay_rate_pct
    FROM flights
    WHERE cancelled = 0
    GROUP BY carrier_code, month
),
carrier_trend AS (
    SELECT
        cm.carrier_code,
        c.carrier_name,
        COUNT(DISTINCT cm.month)                                                AS months_observed,
        ROUND(AVG(cm.delay_rate_pct), 2)                                       AS avg_delay_rate,
        ROUND(MIN(cm.delay_rate_pct), 2)                                       AS best_month_rate,
        ROUND(MAX(cm.delay_rate_pct), 2)                                       AS worst_month_rate,
        -- Regression slope: delay_rate change per month
        ROUND(REGR_SLOPE(cm.delay_rate_pct, cm.month), 4)                     AS trend_slope,
        -- First and last month delay rates
        MIN(cm.delay_rate_pct) FILTER (WHERE cm.month = (
            SELECT MIN(month) FROM carrier_monthly WHERE carrier_code = cm.carrier_code
        ))                                                                      AS first_month_rate,
        MAX(cm.delay_rate_pct) FILTER (WHERE cm.month = (
            SELECT MAX(month) FROM carrier_monthly WHERE carrier_code = cm.carrier_code
        ))                                                                      AS last_month_rate
    FROM carrier_monthly cm
    LEFT JOIN dim_carriers c USING (carrier_code)
    GROUP BY cm.carrier_code, c.carrier_name
)
SELECT
    carrier_code,
    carrier_name,
    months_observed,
    avg_delay_rate,
    best_month_rate,
    worst_month_rate,
    first_month_rate,
    last_month_rate,
    trend_slope,
    CASE
        WHEN trend_slope < -0.5  THEN 'Strongly Improving'
        WHEN trend_slope < -0.1  THEN 'Improving'
        WHEN trend_slope >  0.5  THEN 'Strongly Degrading'
        WHEN trend_slope >  0.1  THEN 'Degrading'
        ELSE 'Stable'
    END                                                                         AS trend_direction,
    RANK() OVER (ORDER BY trend_slope ASC)                                     AS improvement_rank
FROM carrier_trend
ORDER BY trend_slope ASC;


-- ====================================================================
-- END OF ADVANCED ANALYTICS
-- ====================================================================
-- Summary of techniques demonstrated:
--   - Window functions: RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD,
--     NTILE, PERCENT_RANK, CUME_DIST, FIRST_VALUE
--   - Window frames: ROWS BETWEEN, UNBOUNDED PRECEDING, RANGE
--   - CTEs: standard, chained, recursive
--   - Aggregations: FILTER, PERCENTILE_CONT, CORR, REGR_SLOPE,
--     STDDEV, conditional CASE expressions
--   - DuckDB-specific: PIVOT, QUALIFY
--   - Analytical patterns: YoY comparison, rolling averages,
--     composite scoring, cumulative distributions, trend detection
-- ====================================================================
