#!/bin/sh
set -eu

.venv/bin/alembic upgrade head

if [ "${INGEST_ON_STARTUP:-true}" = "true" ]; then
  .venv/bin/python scripts/ingest.py --all --data-dir "${DATA_DIR:-/data}"
fi

exec .venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
