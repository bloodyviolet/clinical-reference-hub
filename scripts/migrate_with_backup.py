#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from config import load_settings
from scripts.db_ops import backup_sqlite


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup then migrate the production SQLite database. Service must be stopped.")
    parser.add_argument("--confirm", required=True, help='Must be exactly "MIGRATE-SERVICE-STOPPED".')
    args = parser.parse_args()
    if args.confirm != "MIGRATE-SERVICE-STOPPED":
        parser.error('Refusing migration: pass --confirm "MIGRATE-SERVICE-STOPPED" after stopping the API.')
    settings = load_settings()
    db_path = database.sqlite_database_path()
    if db_path.exists():
        backup, _ = backup_sqlite(db_path, settings.backup_directory / "pre-migration", prefix="pre-migration", keep=10)
        print(f"pre_migration_backup={backup}")
    database.engine.dispose()
    database.init_db()
    revision = database.assert_schema_current()
    database.assert_database_health(quick_check=True)
    print(f"migration_complete revision={revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
