#!/bin/bash

DB_PATH="data/processed/flights.duckdb"
mkdir -p data/processed

if [ ! -f "$DB_PATH" ]; then
    if [ -n "$DUCKDB_URL" ]; then
        echo "Downloading flights.duckdb via Python requests ..."
        python3 - <<PYEOF
import requests, sys, os
url = os.environ["DUCKDB_URL"]
dest = "data/processed/flights.duckdb"
print(f"GET {url}", flush=True)
r = requests.get(url, stream=True, timeout=120, allow_redirects=True)
r.raise_for_status()
total = 0
with open(dest, "wb") as f:
    for chunk in r.iter_content(chunk_size=1024*1024):
        f.write(chunk)
        total += len(chunk)
print(f"Downloaded {total/1024/1024:.1f} MB", flush=True)
PYEOF
        if [ $? -eq 0 ]; then
            echo "Download complete."
        else
            echo "WARNING: Download failed — API will start without database"
        fi
    else
        echo "WARNING: DUCKDB_URL not set — API will start without database"
    fi
fi

echo "Starting server on port ${PORT:-8000} ..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
