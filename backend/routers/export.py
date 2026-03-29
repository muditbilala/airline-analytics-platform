"""Data-export endpoints (CSV / JSON download)."""

from __future__ import annotations

import io
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.services.query_engine import query_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/export", tags=["export"])

# ---------------------------------------------------------------------------
# Dataset -> SQL mapping
# ---------------------------------------------------------------------------

_DATASET_SQL: dict[str, str] = {
    "overview": """
        SELECT COUNT(*) AS total_flights,
               ROUND(100.0*SUM(CASE WHEN is_delayed=0 AND cancelled=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct,
               ROUND(100.0*SUM(is_delayed)/COUNT(*),2) AS delay_pct,
               ROUND(100.0*SUM(cancelled)/COUNT(*),2) AS cancel_pct,
               ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay_min
        FROM flights
    """,
    "carriers": """
        SELECT f.carrier_code, c.carrier_name, COUNT(*) AS total_flights,
               ROUND(100.0*SUM(CASE WHEN f.is_delayed=0 AND f.cancelled=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct,
               ROUND(100.0*SUM(f.is_delayed)/COUNT(*),2) AS delay_pct,
               ROUND(100.0*SUM(f.cancelled)/COUNT(*),2) AS cancel_pct,
               ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay
        FROM flights f JOIN dim_carriers c USING(carrier_code)
        GROUP BY f.carrier_code, c.carrier_name ORDER BY on_time_pct DESC
    """,
    "airports": """
        SELECT f.origin AS airport_code, COALESCE(a.airport_name, f.origin) AS airport_name,
               COUNT(*) AS total_flights,
               ROUND(100.0*SUM(f.is_delayed)/COUNT(*),2) AS delay_rate,
               ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay
        FROM flights f LEFT JOIN dim_airports a ON f.origin=a.iata_code
        WHERE f.cancelled=0 GROUP BY f.origin, a.airport_name
        HAVING COUNT(*)>=1000 ORDER BY delay_rate DESC
    """,
    "hourly": """
        SELECT hour_of_day AS hour,
               ROUND(100.0*SUM(is_delayed)/COUNT(*),2) AS delay_rate,
               ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay,
               COUNT(*) AS flight_count
        FROM flights WHERE cancelled=0 GROUP BY hour_of_day ORDER BY hour_of_day
    """,
    "causes": """
        SELECT v.cause, v.total_minutes
        FROM (VALUES
            ('Carrier',       (SELECT COALESCE(SUM(carrier_delay),0)       FROM flights WHERE is_delayed=1)),
            ('Weather',       (SELECT COALESCE(SUM(weather_delay),0)       FROM flights WHERE is_delayed=1)),
            ('NAS',           (SELECT COALESCE(SUM(nas_delay),0)           FROM flights WHERE is_delayed=1)),
            ('Security',      (SELECT COALESCE(SUM(security_delay),0)      FROM flights WHERE is_delayed=1)),
            ('Late Aircraft', (SELECT COALESCE(SUM(late_aircraft_delay),0) FROM flights WHERE is_delayed=1))
        ) AS v(cause, total_minutes) ORDER BY v.total_minutes DESC
    """,
    "trends": """
        SELECT year, month,
               ROUND(100.0*SUM(is_delayed)/COUNT(*),2) AS delay_rate,
               ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay,
               COUNT(*) AS total_flights
        FROM flights WHERE cancelled=0 GROUP BY year, month ORDER BY year, month
    """,
    "cancellations": """
        SELECT cancellation_code,
               CASE cancellation_code WHEN 'A' THEN 'Carrier' WHEN 'B' THEN 'Weather'
                    WHEN 'C' THEN 'NAS' WHEN 'D' THEN 'Security' ELSE 'Unknown' END AS reason,
               COUNT(*) AS count
        FROM flights WHERE cancelled=1 GROUP BY cancellation_code ORDER BY count DESC
    """,
}

AVAILABLE_DATASETS = sorted(_DATASET_SQL.keys())


def _get_df(dataset: str):
    """Return a pandas DataFrame for the requested dataset."""
    sql = _DATASET_SQL.get(dataset)
    if sql is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset '{dataset}'. Available: {AVAILABLE_DATASETS}",
        )
    try:
        return query_engine.execute_query_df(sql)
    except Exception as exc:
        logger.exception("Export query failed for dataset=%s", dataset)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _csv_response(dataset: str) -> StreamingResponse:
    """Build a CSV streaming response for the given dataset name."""
    df = _get_df(dataset)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset}.csv"},
    )


# ---------------------------------------------------------------------------
# Dedicated CSV export endpoints
# ---------------------------------------------------------------------------

@router.get("/carriers")
async def export_carriers_csv() -> StreamingResponse:
    """Download carrier performance data as CSV."""
    return _csv_response("carriers")


@router.get("/airports")
async def export_airports_csv() -> StreamingResponse:
    """Download airport performance data as CSV."""
    return _csv_response("airports")


# ---------------------------------------------------------------------------
# Generic export endpoints
# ---------------------------------------------------------------------------

@router.get("/csv")
async def export_csv(
    dataset: str = Query("overview", description="Dataset to export"),
) -> StreamingResponse:
    """Download any available dataset as CSV."""
    return _csv_response(dataset)


@router.get("/json")
async def export_json(
    dataset: str = Query("overview", description="Dataset to export"),
) -> StreamingResponse:
    """Download any available dataset as JSON."""
    df = _get_df(dataset)
    buf = io.StringIO()
    df.to_json(buf, orient="records", indent=2)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={dataset}.json"},
    )
