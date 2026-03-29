"""Rule-based chatbot engine with keyword intent classification.

Maps natural-language questions to pre-defined DuckDB queries and formats
the results with contextual text insights.  An optional LLM integration
point is left as a clearly-marked stub for future enhancement.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from backend.services.query_engine import query_engine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IntentConfig:
    """Defines the SQL, response template, and chart type for an intent."""

    keywords: list[str]
    sql: str
    answer_template: str
    chart_type: str


@dataclass
class ChatbotResult:
    """Structured result returned by the chatbot engine."""

    answer: str
    data: Optional[list[dict[str, Any]]] = None
    chart_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Intent registry
# ---------------------------------------------------------------------------

INTENT_REGISTRY: dict[str, IntentConfig] = {
    "best_airline": IntentConfig(
        keywords=[
            r"best\b.*airline", r"least\b.*delay", r"top.*airline",
            r"most.*on.?time", r"punctual", r"airline.*least",
            r"which.*airline.*best", r"airline.*best",
        ],
        sql="""
            SELECT f.carrier_code, c.carrier_name,
                   COUNT(*) AS total_flights,
                   ROUND(100.0 * SUM(CASE WHEN f.is_delayed=0 AND f.cancelled=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct,
                   ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay
            FROM flights f JOIN dim_carriers c USING(carrier_code)
            GROUP BY f.carrier_code, c.carrier_name
            ORDER BY on_time_pct DESC
        """,
        answer_template="Here are the airlines ranked from best to worst on-time performance:",
        chart_type="bar",
    ),
    "worst_airline": IntentConfig(
        keywords=[
            r"worst\b.*airline", r"most\b.*delay.*airline", r"worst.*carrier",
            r"highest.*delay.*airline",
        ],
        sql="""
            SELECT f.carrier_code, c.carrier_name,
                   COUNT(*) AS total_flights,
                   ROUND(100.0 * SUM(f.is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay
            FROM flights f JOIN dim_carriers c USING(carrier_code)
            GROUP BY f.carrier_code, c.carrier_name
            ORDER BY delay_rate DESC
        """,
        answer_template="Here are the airlines with the highest delay rates:",
        chart_type="bar",
    ),
    "airline_ranking": IntentConfig(
        keywords=[
            r"airline.*rank", r"rank.*airline", r"carrier.*rank", r"compare.*airline",
            r"airline.*performance",
        ],
        sql="""
            SELECT f.carrier_code, c.carrier_name,
                   COUNT(*) AS total_flights,
                   ROUND(100.0 * SUM(CASE WHEN f.is_delayed=0 AND f.cancelled=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct,
                   ROUND(100.0 * SUM(f.is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay
            FROM flights f JOIN dim_carriers c USING(carrier_code)
            GROUP BY f.carrier_code, c.carrier_name
            ORDER BY on_time_pct DESC
        """,
        answer_template="Here is the full airline ranking by on-time performance:",
        chart_type="bar",
    ),
    "peak_delay_hours": IntentConfig(
        keywords=[
            r"peak.*hour", r"busiest.*hour", r"worst.*time", r"best.*time.*fly",
            r"hour.*delay", r"delay.*hour", r"time.*day",
        ],
        sql="""
            SELECT hour_of_day AS hour,
                   ROUND(100.0*SUM(is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay,
                   COUNT(*) AS flight_count
            FROM flights WHERE cancelled=0
            GROUP BY hour_of_day ORDER BY hour_of_day
        """,
        answer_template="Here is the delay pattern across different hours of the day:",
        chart_type="line",
    ),
    "delay_causes": IntentConfig(
        keywords=[
            r"cause", r"reason.*delay", r"why.*delay", r"delay.*because",
            r"what.*cause",
        ],
        sql="""
            SELECT v.cause, v.total_minutes,
                   ROUND(100.0*v.total_minutes / NULLIF(
                       (SELECT COALESCE(SUM(carrier_delay),0)+COALESCE(SUM(weather_delay),0)
                              +COALESCE(SUM(nas_delay),0)+COALESCE(SUM(security_delay),0)
                              +COALESCE(SUM(late_aircraft_delay),0)
                        FROM flights WHERE is_delayed=1), 0), 2) AS percentage
            FROM (VALUES
                ('Carrier',       (SELECT COALESCE(SUM(carrier_delay),0)       FROM flights WHERE is_delayed=1)),
                ('Weather',       (SELECT COALESCE(SUM(weather_delay),0)       FROM flights WHERE is_delayed=1)),
                ('NAS',           (SELECT COALESCE(SUM(nas_delay),0)           FROM flights WHERE is_delayed=1)),
                ('Security',      (SELECT COALESCE(SUM(security_delay),0)      FROM flights WHERE is_delayed=1)),
                ('Late Aircraft', (SELECT COALESCE(SUM(late_aircraft_delay),0) FROM flights WHERE is_delayed=1))
            ) AS v(cause, total_minutes)
            ORDER BY v.total_minutes DESC
        """,
        answer_template="Here is the breakdown of delay causes by total minutes:",
        chart_type="pie",
    ),
    "weather_delays": IntentConfig(
        keywords=[r"weather"],
        sql="""
            SELECT c.season,
                   ROUND(AVG(f.weather_delay),2) AS avg_weather_delay,
                   SUM(CASE WHEN f.weather_delay>0 THEN 1 ELSE 0 END) AS weather_delayed_flights,
                   COUNT(*) AS total_flights
            FROM flights f JOIN dim_calendar c USING(flight_date)
            WHERE f.cancelled=0
            GROUP BY c.season ORDER BY avg_weather_delay DESC
        """,
        answer_template="Here is the weather delay analysis by season:",
        chart_type="bar",
    ),
    "airport_comparison": IntentConfig(
        keywords=[
            r"airport.*compar", r"airport.*delay", r"delay.*airport",
            r"which.*airport.*worst", r"which.*airport.*best",
        ],
        sql="""
            SELECT f.origin AS airport_code, COALESCE(a.airport_name, f.origin) AS airport_name,
                   COUNT(*) AS total_flights,
                   ROUND(100.0*SUM(f.is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay
            FROM flights f LEFT JOIN dim_airports a ON f.origin=a.iata_code
            WHERE f.cancelled=0 GROUP BY f.origin, a.airport_name
            HAVING COUNT(*)>=1000 ORDER BY delay_rate DESC LIMIT 20
        """,
        answer_template="Here are the airports compared by delay rate:",
        chart_type="bar",
    ),
    "busiest_airport": IntentConfig(
        keywords=[
            r"busiest.*airport", r"most.*flights.*airport", r"largest.*airport",
            r"airport.*volume", r"airport.*traffic",
        ],
        sql="""
            SELECT f.origin AS airport_code, COALESCE(a.airport_name, f.origin) AS airport_name,
                   COUNT(*) AS total_flights
            FROM flights f LEFT JOIN dim_airports a ON f.origin=a.iata_code
            GROUP BY f.origin, a.airport_name
            ORDER BY total_flights DESC LIMIT 20
        """,
        answer_template="Here are the busiest airports by flight volume:",
        chart_type="bar",
    ),
    "cancellation_info": IntentConfig(
        keywords=[r"cancel", r"cancell"],
        sql="""
            SELECT
                cancellation_code,
                CASE cancellation_code WHEN 'A' THEN 'Carrier' WHEN 'B' THEN 'Weather'
                     WHEN 'C' THEN 'NAS' WHEN 'D' THEN 'Security' ELSE 'Unknown' END AS reason,
                COUNT(*) AS count
            FROM flights WHERE cancelled=1
            GROUP BY cancellation_code ORDER BY count DESC
        """,
        answer_template="Here is the cancellation breakdown by reason:",
        chart_type="pie",
    ),
    "monthly_trends": IntentConfig(
        keywords=[r"monthly.*trend", r"trend", r"month"],
        sql="""
            SELECT year, month,
                   ROUND(100.0*SUM(is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay,
                   COUNT(*) AS total_flights
            FROM flights WHERE cancelled=0
            GROUP BY year, month ORDER BY year, month
        """,
        answer_template="Here are the monthly delay trends:",
        chart_type="line",
    ),
    "seasonal": IntentConfig(
        keywords=[r"season", r"day.*week", r"weekday", r"weekend"],
        sql="""
            SELECT c.season,
                   ROUND(100.0*SUM(f.is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN f.arr_delay_minutes>0 THEN f.arr_delay_minutes END),2) AS avg_delay,
                   COUNT(*) AS total_flights
            FROM flights f JOIN dim_calendar c USING(flight_date)
            WHERE f.cancelled=0
            GROUP BY c.season ORDER BY delay_rate DESC
        """,
        answer_template="Here are the seasonal delay patterns:",
        chart_type="bar",
    ),
    "route_analysis": IntentConfig(
        keywords=[r"route", r"origin.*dest", r"city.*pair"],
        sql="""
            SELECT route, origin, dest,
                   COUNT(*) AS total_flights,
                   ROUND(100.0*SUM(is_delayed)/COUNT(*),2) AS delay_rate,
                   ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay
            FROM flights WHERE cancelled=0
            GROUP BY route, origin, dest HAVING COUNT(*)>=500
            ORDER BY delay_rate DESC LIMIT 20
        """,
        answer_template="Here are the routes with the highest delay rates:",
        chart_type="bar",
    ),
    "general_stats": IntentConfig(
        keywords=[r"overview", r"summary", r"general", r"stats", r"statistic", r"how many"],
        sql="""
            SELECT COUNT(*) AS total_flights,
                   ROUND(100.0*SUM(CASE WHEN is_delayed=0 AND cancelled=0 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct,
                   ROUND(100.0*SUM(CASE WHEN is_delayed=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS delay_pct,
                   ROUND(100.0*SUM(CASE WHEN cancelled=1 THEN 1 ELSE 0 END)/COUNT(*),2) AS cancel_pct,
                   ROUND(AVG(CASE WHEN arr_delay_minutes>0 THEN arr_delay_minutes END),2) AS avg_delay_min
            FROM flights
        """,
        answer_template="Here is a general overview of the flight dataset:",
        chart_type="kpi",
    ),
}

# The overview intent is the default fallback (no keywords needed).
_FALLBACK_INTENT = "general_stats"

# Sample questions the frontend can show users.
SAMPLE_SUGGESTIONS: list[str] = [
    "Which airline has the best on-time performance?",
    "What are the main causes of flight delays?",
    "Which hours have the worst delays?",
    "Show me monthly delay trends",
    "Which airports have the highest delay rate?",
    "What is the cancellation breakdown?",
    "How does weather affect delays?",
    "What are the busiest airports?",
    "Show me the worst routes for delays",
    "Give me an overview of all flights",
]


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

def classify_intent(text: str) -> str:
    """Match the user's query against keyword patterns and return intent key.

    Iterates through the registry in insertion order.  The first intent whose
    keyword regex matches wins.  If nothing matches, ``_FALLBACK_INTENT`` is
    returned.
    """
    lower = text.lower().strip()
    for intent, cfg in INTENT_REGISTRY.items():
        for pattern in cfg.keywords:
            if re.search(pattern, lower):
                return intent
    return _FALLBACK_INTENT


# ---------------------------------------------------------------------------
# Query execution + response formatting
# ---------------------------------------------------------------------------

def _format_insight(intent: str, rows: list[dict[str, Any]]) -> str:
    """Generate a short textual insight to accompany the data."""
    if not rows:
        return "No data found for your query."

    # Add contextual detail for some common intents
    if intent in ("best_airline", "airline_ranking") and len(rows) >= 1:
        top = rows[0]
        return (
            f"{top.get('carrier_name', 'N/A')} leads with "
            f"{top.get('on_time_pct', 'N/A')}% on-time performance "
            f"across {top.get('total_flights', 'N/A'):,} flights."
        )

    if intent == "worst_airline" and len(rows) >= 1:
        top = rows[0]
        return (
            f"{top.get('carrier_name', 'N/A')} has the highest delay rate at "
            f"{top.get('delay_rate', 'N/A')}%."
        )

    if intent == "peak_delay_hours" and len(rows) >= 1:
        worst = max(rows, key=lambda r: r.get("delay_rate", 0))
        return (
            f"Hour {worst.get('hour', '?')}:00 has the highest delay rate at "
            f"{worst.get('delay_rate', 'N/A')}%."
        )

    if intent == "delay_causes" and len(rows) >= 1:
        top = rows[0]
        return (
            f"'{top.get('cause', 'N/A')}' is the leading delay cause, "
            f"accounting for {top.get('percentage', 'N/A')}% of total delay minutes."
        )

    if intent == "general_stats" and len(rows) >= 1:
        r = rows[0]
        return (
            f"The dataset contains {r.get('total_flights', 'N/A'):,} flights. "
            f"On-time: {r.get('on_time_pct', 'N/A')}%, "
            f"Delayed: {r.get('delay_pct', 'N/A')}%, "
            f"Cancelled: {r.get('cancel_pct', 'N/A')}%."
        )

    return ""


_FALLBACK_MESSAGE = (
    "I can help you with questions about:\n"
    "- Airline rankings and performance\n"
    "- Peak delay hours and times to fly\n"
    "- Delay causes (weather, carrier, NAS, etc.)\n"
    "- Airport comparisons and busiest airports\n"
    "- Cancellation analysis\n"
    "- Monthly and seasonal trends\n"
    "- Route analysis\n"
    "- General flight statistics\n\n"
    "Try asking something like: 'Which airline has the best on-time performance?'"
)


def process_query(message: str) -> ChatbotResult:
    """Classify intent, run the corresponding query, and return a result.

    Parameters
    ----------
    message:
        The user's natural-language question.

    Returns
    -------
    ChatbotResult
        Contains the answer text, optional data rows, and chart type hint.
    """
    intent = classify_intent(message)
    cfg = INTENT_REGISTRY[intent]
    logger.info("Chatbot intent=%s for message=%r", intent, message[:80])

    try:
        rows = query_engine.execute_query(cfg.sql)
    except Exception:
        logger.exception("Chatbot query execution failed for intent=%s", intent)
        return ChatbotResult(
            answer="Sorry, I encountered an error while fetching the data. Please try again.",
        )

    insight = _format_insight(intent, rows)
    answer = cfg.answer_template
    if insight:
        answer = f"{answer}\n\n{insight}"

    return ChatbotResult(answer=answer, data=rows, chart_type=cfg.chart_type)
