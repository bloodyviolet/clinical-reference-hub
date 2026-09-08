#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from config import load_settings
from scripts.db_ops import alembic_revision, backup_sqlite, restore_sqlite, sqlite_integrity, verify_backup_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a verified SQLite backup. Run only while the API service is stopped.")
    parser.add_argument("backup", type=Path)
    parser.add_argument("--confirm", required=True, help='Must be exactly "RESTORE-SERVICE-STOPPED".')
    parser.add_argument("--allow-schema-mismatch", action="store_true")
    args = parser.parse_args()
    if args.confirm != "RESTORE-SERVICE-STOPPED":
        parser.error('Refusing restore: pass --confirm "RESTORE-SERVICE-STOPPED" only after stopping the API.')

    ok, detail = sqlite_integrity(args.backup)
    if not ok:
        raise SystemExit(f"Backup integrity failed: {detail}")
    meta_ok, meta_detail = verify_backup_metadata(args.backup)
    if not meta_ok:
        raise SystemExit(f"Backup metadata validation failed: {meta_detail}")
    revision = alembic_revision(args.backup)
    expected = database.current_migration_head()
    if revision != expected and not args.allow_schema_mismatch:
        raise SystemExit(f"Backup revision {revision or '<none>'} does not match application head {expected}.")

    destination = database.sqlite_database_path()
    settings = load_settings()
    if destination.exists():
        pre, _ = backup_sqlite(destination, settings.backup_directory / "pre-restore", prefix="pre-restore", keep=10)
        print(f"pre_restore_backup={pre}")
    database.engine.dispose()
    restore_sqlite(args.backup, destination)
    print(f"restored={destination}")
    print(f"revision={alembic_revision(destination)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
