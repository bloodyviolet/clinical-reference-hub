#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from scripts.db_ops import alembic_revision, sha256_file, sqlite_integrity, verify_backup_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify SQLite backup integrity and application schema revision.")
    parser.add_argument("backup", type=Path)
    parser.add_argument("--allow-schema-mismatch", action="store_true")
    args = parser.parse_args()
    ok, detail = sqlite_integrity(args.backup)
    if not ok:
        print(f"FAIL integrity={detail}", file=sys.stderr)
        return 2
    meta_ok, meta_detail = verify_backup_metadata(args.backup)
    if not meta_ok:
        print(f"FAIL metadata={meta_detail}", file=sys.stderr)
        return 4
    revision = alembic_revision(args.backup)
    expected = database.current_migration_head()
    if revision != expected and not args.allow_schema_mismatch:
        print(f"FAIL revision={revision or '<none>'} expected={expected}", file=sys.stderr)
        return 3
    print(f"OK integrity={detail} metadata={meta_detail} revision={revision or '<none>'} sha256={sha256_file(args.backup)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
