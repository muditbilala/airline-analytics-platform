"""Thread-safe DuckDB query engine with connection pooling and safety guards."""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any, Generator, Optional

import duckdb
import pandas as pd

from backend.config import DUCKDB_PATH, MAX_QUERY_ROWS, QUERY_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class QueryEngine:
    """Manages read-only DuckDB connections with per-thread isolation."""

    def __init__(self, db_path: str | None = None, max_rows: int = MAX_QUERY_ROWS) -> None:
        self._db_path = str(db_path or DUCKDB_PATH)
        self._max_rows = max_rows
        self._local = threading.local()
        logger.info("QueryEngine initialised – db=%s, max_rows=%d", self._db_path, self._max_rows)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Return a per-thread connection, creating one if needed."""
        conn: Optional[duckdb.DuckDBPyConnection] = getattr(self._local, "conn", None)
        if conn is None:
            conn = duckdb.connect(self._db_path, read_only=True)
            # Set memory limit as a safety guard
            try:
                conn.execute(f"SET memory_limit='2GB'")
            except Exception:
                pass  # Ignore if not supported
            self._local.conn = conn
            logger.debug("New DuckDB connection on thread %s", threading.current_thread().name)
        return conn

    @contextmanager
    def connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Context manager that yields a thread-local connection."""
        yield self._get_connection()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def execute_query(
        self,
        sql: str,
        params: Optional[list[Any]] = None,
        max_rows: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Execute *sql* and return a list of dicts (capped at *max_rows*)."""
        limit = max_rows or self._max_rows
        wrapped = f"SELECT * FROM ({sql}) AS _q LIMIT {limit}"
        conn = self._get_connection()
        try:
            result = conn.execute(wrapped, params or [])
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception:
            logger.exception("execute_query failed – sql=%s", sql[:200])
            raise

    def execute_query_df(
        self,
        sql: str,
        params: Optional[list[Any]] = None,
        max_rows: Optional[int] = None,
    ) -> pd.DataFrame:
        """Execute *sql* and return a pandas DataFrame (capped at *max_rows*)."""
        limit = max_rows or self._max_rows
        wrapped = f"SELECT * FROM ({sql}) AS _q LIMIT {limit}"
        conn = self._get_connection()
        try:
            return conn.execute(wrapped, params or []).fetchdf()
        except Exception:
            logger.exception("execute_query_df failed – sql=%s", sql[:200])
            raise

    def health_check(self) -> bool:
        """Return True if the database is reachable."""
        try:
            rows = self.execute_query("SELECT 1 AS ok", max_rows=1)
            return rows[0]["ok"] == 1
        except Exception:
            logger.exception("Health check failed")
            return False

    def close_all(self) -> None:
        """Close the thread-local connection if it exists."""
        conn: Optional[duckdb.DuckDBPyConnection] = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
            logger.debug("Closed DuckDB connection on thread %s", threading.current_thread().name)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

query_engine = QueryEngine()
