#!/bin/bash

DB_PATH="data/processed/flights.duckdb"
mkdir -p data/processed

if [ ! -f "$DB_PATH" ]; then
    if [ -n "$DUCKDB_URL" ]; then
        echo "Downloading flights.duckdb ..."
        curl -L --retry 3 --retry-delay 5 -o "$DB_PATH" "$DUCKDB_URL" \
          && echo "Download complete: $(du -sh $DB_PATH | cut -f1)" \
          || echo "WARNING: Download failed — API will start without database"
    else
        echo "WARNING: DUCKDB_URL not set — API will start without database"
    fi
fi

echo "Starting server on port ${PORT:-8000} ..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
