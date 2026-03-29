"""FastAPI application entry-point for the Flight Delay Analytics API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import API_HOST, API_PORT, CORS_ORIGINS
from backend.models.schemas import APIResponse
from backend.routers import analytics, chatbot, export
from backend.services.query_engine import query_engine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Verify DuckDB connectivity on startup; clean up on shutdown."""
    logger.info("Starting Flight Delay Analytics API ...")
    if query_engine.health_check():
        logger.info("DuckDB connection verified successfully.")
    else:
        logger.error("DuckDB health check FAILED — the database may be unavailable.")
    yield
    query_engine.close_all()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Flight Delay Analytics API",
    description="REST API for exploring US domestic flight delay data.",
    version="1.0.0",
    lifespan=lifespan,
)

# -- CORS ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers ---------------------------------------------------------------

app.include_router(analytics.router)
app.include_router(chatbot.router)
app.include_router(export.router)


# -- Global error handler --------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler so unhandled errors still return structured JSON."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "message": f"Internal server error: {exc}"},
    )


# -- Health check -----------------------------------------------------------

@app.get("/health", response_model=APIResponse[dict], tags=["system"])
async def health() -> APIResponse[dict]:
    """Lightweight health/readiness probe."""
    db_ok = query_engine.health_check()
    status = "healthy" if db_ok else "degraded"
    return APIResponse(
        success=db_ok,
        data={"status": status, "database": "connected" if db_ok else "unreachable"},
        message=status,
    )


@app.get("/", tags=["system"])
async def root() -> dict:
    """Landing page with API information."""
    return {
        "name": "Flight Delay Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Direct execution (uvicorn)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=True)
