#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from scripts.db_ops import sqlite_integrity


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialise a runtime SQLite database from the packaged release database.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    source = ROOT / "medical.db"
    destination = database.sqlite_database_path()
    if source.resolve() == destination.resolve():
        print(f"runtime database already uses packaged path: {destination}")
        return 0
    if destination.exists() and not args.overwrite:
        print(f"runtime database already exists: {destination}")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    ok, detail = sqlite_integrity(destination)
    if not ok:
        destination.unlink(missing_ok=True)
        raise SystemExit(f"Copied database failed integrity check: {detail}")
    print(f"initialised={destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
