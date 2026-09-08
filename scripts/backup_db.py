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
    parser = argparse.ArgumentParser(description="Create an online-consistent SQLite backup and SHA-256 metadata file.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--keep", type=int, default=14, help="Retain this many most-recent backups (0 disables pruning).")
    parser.add_argument("--prefix", default="medical-api")
    args = parser.parse_args()
    settings = load_settings()
    output = args.output_dir or settings.backup_directory
    backup, metadata = backup_sqlite(database.sqlite_database_path(), output, prefix=args.prefix, keep=args.keep or None)
    print(f"backup={backup}")
    print(f"metadata={metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
