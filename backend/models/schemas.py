"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic API wrapper
# ---------------------------------------------------------------------------

class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for every API response."""

    success: bool = True
    data: T
    message: str = "OK"
    count: Optional[int] = None


# ---------------------------------------------------------------------------
# KPI / Overview
# ---------------------------------------------------------------------------

class KPIOverview(BaseModel):
    total_flights: int
    on_time_pct: float = Field(..., description="Percentage of on-time flights")
    delay_pct: float = Field(..., description="Percentage of delayed flights")
    cancel_pct: float = Field(..., description="Percentage of cancelled flights")
    avg_delay_min: float = Field(..., description="Average delay in minutes (delayed flights only)")


# ---------------------------------------------------------------------------
# Delay analytics
# ---------------------------------------------------------------------------

class DelayByHour(BaseModel):
    hour: int
    delay_rate: float
    avg_delay: float
    flight_count: int


class CarrierPerformance(BaseModel):
    carrier_code: str
    carrier_name: str
    total_flights: int
    on_time_pct: float
    avg_delay: float
    rank: int


class AirportPerformance(BaseModel):
    airport_code: str
    airport_name: str
    total_flights: int
    delay_rate: float
    avg_delay: float


class DelayCause(BaseModel):
    cause: str
    total_minutes: float
    percentage: float


class MonthlyTrend(BaseModel):
    year: int
    month: int
    delay_rate: float
    avg_delay: float
    total_flights: int


class SeasonalPattern(BaseModel):
    season: str
    delay_rate: float
    avg_delay: float
    total_flights: int


class HeatmapCell(BaseModel):
    hour: int
    day_of_week: int
    delay_rate: float
    flight_count: int


class DayOfWeekPattern(BaseModel):
    day_of_week: int
    day_name: str
    delay_rate: float
    avg_delay: float
    total_flights: int


class CarrierRanking(BaseModel):
    carrier_code: str
    carrier_name: str
    total_flights: int
    on_time_pct: float
    delay_pct: float
    cancel_pct: float
    avg_delay: float
    rank: int


class RoutePerformance(BaseModel):
    route: str
    origin: str
    dest: str
    total_flights: int
    delay_rate: float
    avg_delay: float


class CancellationSummary(BaseModel):
    cancellation_code: Optional[str]
    reason: str
    count: int
    percentage: float


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------

class ChatbotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="Natural-language question")


class ChatbotResponse(BaseModel):
    answer: str
    data: Optional[List[dict[str, Any]]] = None
    chart_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class ExportParams(BaseModel):
    dataset: str = Field("overview", description="Dataset to export")
