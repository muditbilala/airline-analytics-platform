"""Analytics API endpoints for flight-delay data."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    APIResponse,
    AirportPerformance,
    CancellationSummary,
    CarrierPerformance,
    CarrierRanking,
    DayOfWeekPattern,
    DelayCause,
    DelayByHour,
    HeatmapCell,
    KPIOverview,
    MonthlyTrend,
    RoutePerformance,
)
from backend.services.query_engine import query_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(sql: str, max_rows: int | None = None) -> list[dict]:
    """Thin wrapper that converts query errors to 500s."""
    try:
        return query_engine.execute_query(sql, max_rows=max_rows)
    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=APIResponse[KPIOverview])
async def get_overview() -> APIResponse[KPIOverview]:
    """Return high-level KPI summary across all flights."""
    sql = """
        SELECT
            COUNT(*)                                                AS total_flights,
            ROUND(100.0 * SUM(CASE WHEN is_delayed = 0 AND cancelled = 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS on_time_pct,
            ROUND(100.0 * SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS delay_pct,
            ROUND(100.0 * SUM(CASE WHEN cancelled = 1 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS cancel_pct,
            ROUND(AVG(CASE WHEN arr_delay_minutes > 0 THEN arr_delay_minutes END), 2)
                                                                     AS avg_delay_min
        FROM flights
    """
    rows = _run(sql)
    return APIResponse(data=KPIOverview(**rows[0]))


@router.get("/delays/by-hour", response_model=APIResponse[list[DelayByHour]])
async def get_delays_by_hour() -> APIResponse[list[DelayByHour]]:
    """Delay rate and average delay grouped by hour of day."""
    sql = """
        SELECT
            hour_of_day                                             AS hour,
            ROUND(100.0 * SUM(is_delayed) / COUNT(*), 2)           AS delay_rate,
            ROUND(AVG(CASE WHEN arr_delay_minutes > 0 THEN arr_delay_minutes END), 2)
                                                                     AS avg_delay,
            COUNT(*)                                                AS flight_count
        FROM flights
        WHERE cancelled = 0
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """
    rows = _run(sql, max_rows=24)
    return APIResponse(data=[DelayByHour(**r) for r in rows], count=len(rows))


@router.get("/delays/by-carrier", response_model=APIResponse[list[CarrierPerformance]])
async def get_delays_by_carrier() -> APIResponse[list[CarrierPerformance]]:
    """Carrier ranking by on-time performance."""
    sql = """
        SELECT
            f.carrier_code,
            c.carrier_name,
            COUNT(*)                                                AS total_flights,
            ROUND(100.0 * SUM(CASE WHEN f.is_delayed = 0 AND f.cancelled = 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS on_time_pct,
            ROUND(AVG(CASE WHEN f.arr_delay_minutes > 0 THEN f.arr_delay_minutes END), 2)
                                                                     AS avg_delay,
            ROW_NUMBER() OVER (ORDER BY
                100.0 * SUM(CASE WHEN f.is_delayed = 0 AND f.cancelled = 0 THEN 1 ELSE 0 END) / COUNT(*) DESC
            )                                                        AS rank
        FROM flights f
        JOIN dim_carriers c USING (carrier_code)
        GROUP BY f.carrier_code, c.carrier_name
        ORDER BY rank
    """
    rows = _run(sql, max_rows=50)
    return APIResponse(data=[CarrierPerformance(**r) for r in rows], count=len(rows))


@router.get("/delays/by-airport", response_model=APIResponse[list[AirportPerformance]])
async def get_delays_by_airport(
    limit: int = Query(20, ge=1, le=100, description="Number of airports to return"),
) -> APIResponse[list[AirportPerformance]]:
    """Airport comparison ranked by delay rate."""
    sql = f"""
        SELECT
            f.origin                                                AS airport_code,
            COALESCE(a.airport_name, f.origin)                      AS airport_name,
            COUNT(*)                                                AS total_flights,
            ROUND(100.0 * SUM(f.is_delayed) / COUNT(*), 2)         AS delay_rate,
            ROUND(AVG(CASE WHEN f.arr_delay_minutes > 0 THEN f.arr_delay_minutes END), 2)
                                                                     AS avg_delay
        FROM flights f
        LEFT JOIN dim_airports a ON f.origin = a.iata_code
        WHERE f.cancelled = 0
        GROUP BY f.origin, a.airport_name
        HAVING COUNT(*) >= 1000
        ORDER BY delay_rate DESC
        LIMIT {limit}
    """
    rows = _run(sql, max_rows=limit)
    return APIResponse(data=[AirportPerformance(**r) for r in rows], count=len(rows))


@router.get("/delays/causes", response_model=APIResponse[list[DelayCause]])
async def get_delay_causes() -> APIResponse[list[DelayCause]]:
    """Breakdown of delay minutes by cause category."""
    sql = """
        WITH totals AS (
            SELECT
                COALESCE(SUM(carrier_delay), 0)
                    + COALESCE(SUM(weather_delay), 0)
                    + COALESCE(SUM(nas_delay), 0)
                    + COALESCE(SUM(security_delay), 0)
                    + COALESCE(SUM(late_aircraft_delay), 0) AS grand_total
            FROM flights
            WHERE is_delayed = 1
        )
        SELECT cause, total_minutes,
               ROUND(100.0 * total_minutes / NULLIF(t.grand_total, 0), 2) AS percentage
        FROM totals t,
        (VALUES
            ('Carrier',        (SELECT COALESCE(SUM(carrier_delay), 0)        FROM flights WHERE is_delayed = 1)),
            ('Weather',        (SELECT COALESCE(SUM(weather_delay), 0)        FROM flights WHERE is_delayed = 1)),
            ('NAS',            (SELECT COALESCE(SUM(nas_delay), 0)            FROM flights WHERE is_delayed = 1)),
            ('Security',       (SELECT COALESCE(SUM(security_delay), 0)       FROM flights WHERE is_delayed = 1)),
            ('Late Aircraft',  (SELECT COALESCE(SUM(late_aircraft_delay), 0)  FROM flights WHERE is_delayed = 1))
        ) AS v(cause, total_minutes)
        ORDER BY total_minutes DESC
    """
    rows = _run(sql)
    return APIResponse(data=[DelayCause(**r) for r in rows], count=len(rows))


@router.get("/delays/trends", response_model=APIResponse[list[MonthlyTrend]])
async def get_monthly_trends() -> APIResponse[list[MonthlyTrend]]:
    """Monthly delay trends over time."""
    sql = """
        SELECT
            year,
            month,
            ROUND(100.0 * SUM(is_delayed) / COUNT(*), 2)           AS delay_rate,
            ROUND(AVG(CASE WHEN arr_delay_minutes > 0 THEN arr_delay_minutes END), 2)
                                                                     AS avg_delay,
            COUNT(*)                                                AS total_flights
        FROM flights
        WHERE cancelled = 0
        GROUP BY year, month
        ORDER BY year, month
    """
    rows = _run(sql, max_rows=120)
    return APIResponse(data=[MonthlyTrend(**r) for r in rows], count=len(rows))


@router.get("/delays/seasonal", response_model=APIResponse[list[DayOfWeekPattern]])
async def get_seasonal_patterns() -> APIResponse[list[DayOfWeekPattern]]:
    """Day-of-week delay patterns for seasonal analysis."""
    sql = """
        SELECT
            day_of_week,
            CASE day_of_week
                WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' WHEN 6 THEN 'Saturday'
                WHEN 7 THEN 'Sunday' ELSE 'Unknown'
            END                                                     AS day_name,
            ROUND(100.0 * SUM(is_delayed) / COUNT(*), 2)           AS delay_rate,
            ROUND(AVG(CASE WHEN arr_delay_minutes > 0 THEN arr_delay_minutes END), 2)
                                                                     AS avg_delay,
            COUNT(*)                                                AS total_flights
        FROM flights
        WHERE cancelled = 0
        GROUP BY day_of_week
        ORDER BY day_of_week
    """
    rows = _run(sql, max_rows=7)
    return APIResponse(data=[DayOfWeekPattern(**r) for r in rows], count=len(rows))


@router.get("/delays/heatmap", response_model=APIResponse[list[HeatmapCell]])
async def get_delay_heatmap() -> APIResponse[list[HeatmapCell]]:
    """Hour x day-of-week delay-rate crosstab for heatmap visualisation."""
    sql = """
        SELECT
            hour_of_day                                             AS hour,
            day_of_week,
            ROUND(100.0 * SUM(is_delayed) / COUNT(*), 2)           AS delay_rate,
            COUNT(*)                                                AS flight_count
        FROM flights
        WHERE cancelled = 0
        GROUP BY hour_of_day, day_of_week
        ORDER BY hour_of_day, day_of_week
    """
    rows = _run(sql, max_rows=200)
    return APIResponse(data=[HeatmapCell(**r) for r in rows], count=len(rows))


@router.get("/routes/top", response_model=APIResponse[list[RoutePerformance]])
async def get_top_routes(
    sort: str = Query("worst", pattern="^(best|worst)$", description="Sort by best or worst delay rate"),
    limit: int = Query(20, ge=1, le=100),
) -> APIResponse[list[RoutePerformance]]:
    """Best or worst routes by delay rate (min 500 flights)."""
    order = "DESC" if sort == "worst" else "ASC"
    sql = f"""
        SELECT
            route,
            origin,
            dest,
            COUNT(*)                                                AS total_flights,
            ROUND(100.0 * SUM(is_delayed) / COUNT(*), 2)           AS delay_rate,
            ROUND(AVG(CASE WHEN arr_delay_minutes > 0 THEN arr_delay_minutes END), 2)
                                                                     AS avg_delay
        FROM flights
        WHERE cancelled = 0
        GROUP BY route, origin, dest
        HAVING COUNT(*) >= 500
        ORDER BY delay_rate {order}
        LIMIT {limit}
    """
    rows = _run(sql, max_rows=limit)
    return APIResponse(data=[RoutePerformance(**r) for r in rows], count=len(rows))


@router.get("/cancellations", response_model=APIResponse[list[CancellationSummary]])
async def get_cancellations() -> APIResponse[list[CancellationSummary]]:
    """Cancellation analysis by reason code."""
    sql = """
        WITH total AS (
            SELECT COUNT(*) AS cnt FROM flights WHERE cancelled = 1
        )
        SELECT
            f.cancellation_code,
            CASE f.cancellation_code
                WHEN 'A' THEN 'Carrier'
                WHEN 'B' THEN 'Weather'
                WHEN 'C' THEN 'NAS'
                WHEN 'D' THEN 'Security'
                ELSE 'Unknown'
            END                                                     AS reason,
            COUNT(*)                                                AS count,
            ROUND(100.0 * COUNT(*) / NULLIF(t.cnt, 0), 2)          AS percentage
        FROM flights f, total t
        WHERE f.cancelled = 1
        GROUP BY f.cancellation_code, t.cnt
        ORDER BY count DESC
    """
    rows = _run(sql)
    return APIResponse(data=[CancellationSummary(**r) for r in rows], count=len(rows))


@router.get("/carriers/ranking", response_model=APIResponse[list[CarrierRanking]])
async def get_carrier_ranking() -> APIResponse[list[CarrierRanking]]:
    """Full carrier ranking with on-time, delay, and cancellation rates."""
    sql = """
        SELECT
            f.carrier_code,
            c.carrier_name,
            COUNT(*)                                                AS total_flights,
            ROUND(100.0 * SUM(CASE WHEN f.is_delayed = 0 AND f.cancelled = 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS on_time_pct,
            ROUND(100.0 * SUM(CASE WHEN f.is_delayed = 1 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS delay_pct,
            ROUND(100.0 * SUM(CASE WHEN f.cancelled = 1 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                                     AS cancel_pct,
            ROUND(AVG(CASE WHEN f.arr_delay_minutes > 0 THEN f.arr_delay_minutes END), 2)
                                                                     AS avg_delay,
            ROW_NUMBER() OVER (ORDER BY
                100.0 * SUM(CASE WHEN f.is_delayed = 0 AND f.cancelled = 0 THEN 1 ELSE 0 END) / COUNT(*) DESC
            )                                                        AS rank
        FROM flights f
        JOIN dim_carriers c USING (carrier_code)
        GROUP BY f.carrier_code, c.carrier_name
        ORDER BY rank
    """
    rows = _run(sql, max_rows=50)
    return APIResponse(data=[CarrierRanking(**r) for r in rows], count=len(rows))
