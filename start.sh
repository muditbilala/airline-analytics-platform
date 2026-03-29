#!/bin/bash
set -e

DB_PATH="data/processed/flights.duckdb"
mkdir -p data/processed

# Download DuckDB from GitHub Release if not present and URL is provided
if [ ! -f "$DB_PATH" ]; then
    if [ -n "$DUCKDB_URL" ]; then
        echo "Downloading flights.duckdb from $DUCKDB_URL ..."
        curl -L -o "$DB_PATH" "$DUCKDB_URL"
        echo "Download complete. Size: $(du -sh $DB_PATH | cut -f1)"
    else
        echo "WARNING: flights.duckdb not found and DUCKDB_URL not set."
        echo "API will start but database queries will fail."
        echo "Set DUCKDB_URL environment variable to a direct download link."
    fi
fi

echo "Starting FastAPI server on port ${PORT:-8000} ..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
