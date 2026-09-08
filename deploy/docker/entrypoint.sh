#!/bin/sh
set -eu
cd /app
python scripts/init_runtime_db.py
if [ "${MEDICAL_API_AUTO_MIGRATE:-false}" = "true" ]; then
  python scripts/migrate_with_backup.py --confirm MIGRATE-SERVICE-STOPPED
fi
exec /app/scripts/prod_start.sh
