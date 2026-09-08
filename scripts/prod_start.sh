#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
PYTHON_BIN=${MEDICAL_API_PYTHON:-python}
"$PYTHON_BIN" scripts/preflight.py
exec "$PYTHON_BIN" -m uvicorn main:app \
  --host "${MEDICAL_API_BIND_HOST:-127.0.0.1}" \
  --port "${MEDICAL_API_PORT:-8000}" \
  --workers "${MEDICAL_API_WORKERS:-1}" \
  --proxy-headers \
  --forwarded-allow-ips "${MEDICAL_API_TRUSTED_PROXIES:-127.0.0.1,::1}" \
  --timeout-graceful-shutdown "${MEDICAL_API_GRACEFUL_SHUTDOWN_SECONDS:-30}" \
  --limit-concurrency "${MEDICAL_API_LIMIT_CONCURRENCY:-200}" \
  --backlog "${MEDICAL_API_BACKLOG:-1024}" \
  --timeout-keep-alive "${MEDICAL_API_KEEP_ALIVE_SECONDS:-5}" \
  --no-access-log
