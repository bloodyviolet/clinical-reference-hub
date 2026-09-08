"""SQLite backup/restore helpers used by production maintenance scripts."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def verify_backup_metadata(path: Path) -> tuple[bool, str]:
    """Validate adjacent backup metadata when present; absence is reported but not corruption."""
    metadata_path = path.with_suffix(path.suffix + ".json")
    if not metadata_path.is_file():
        return True, "metadata absent"
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"invalid metadata: {exc}"
    actual = sha256_file(path)
    expected = str(payload.get("sha256", ""))
    if not expected or actual != expected:
        return False, f"sha256 mismatch expected={expected or '<missing>'} actual={actual}"
    if payload.get("size_bytes") != path.stat().st_size:
        return False, "backup size does not match metadata"
    return True, "metadata sha256/size verified"

def sqlite_integrity(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "file does not exist"
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
        try:
            result = connection.execute("PRAGMA quick_check").fetchone()
            value = result[0] if result else "no result"
            return value == "ok", str(value)
        finally:
            connection.close()
    except sqlite3.Error as exc:
        return False, str(exc)


def alembic_revision(path: Path) -> str:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "alembic_version" not in tables:
            return ""
        row = connection.execute("SELECT version_num FROM alembic_version LIMIT 1").fetchone()
        return str(row[0]) if row else ""
    finally:
        connection.close()


def backup_sqlite(source: Path, output_dir: Path, *, prefix: str = "medical", keep: int | None = None) -> tuple[Path, Path]:
    source = source.resolve()
    if not source.is_file():
        raise RuntimeError(f"Database does not exist: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = output_dir / f"{prefix}-{timestamp}.sqlite3"
    counter = 1
    while destination.exists():
        destination = output_dir / f"{prefix}-{timestamp}-{counter}.sqlite3"
        counter += 1
    temp = destination.with_suffix(destination.suffix + ".tmp")

    src = sqlite3.connect(str(source), timeout=30)
    dst = sqlite3.connect(str(temp), timeout=30)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    ok, detail = sqlite_integrity(temp)
    if not ok:
        temp.unlink(missing_ok=True)
        raise RuntimeError(f"Backup integrity check failed: {detail}")
    os.replace(temp, destination)

    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "filename": destination.name,
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
        "alembic_revision": alembic_revision(destination),
        "integrity_check": detail,
    }
    metadata_path = destination.with_suffix(destination.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if keep is not None and keep > 0:
        backups = sorted(output_dir.glob(f"{prefix}-*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[keep:]:
            old.unlink(missing_ok=True)
            old.with_suffix(old.suffix + ".json").unlink(missing_ok=True)
    return destination, metadata_path


def restore_sqlite(backup: Path, destination: Path) -> None:
    backup = backup.resolve()
    destination = destination.resolve()
    ok, detail = sqlite_integrity(backup)
    if not ok:
        raise RuntimeError(f"Refusing corrupt/invalid backup: {detail}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".restore.tmp")
    shutil.copy2(backup, temp)
    ok, detail = sqlite_integrity(temp)
    if not ok:
        temp.unlink(missing_ok=True)
        raise RuntimeError(f"Copied restore candidate failed integrity check: {detail}")
    os.replace(temp, destination)
    # A restore is only supported while the service is stopped; stale sidecars must not survive.
    for suffix in ("-wal", "-shm", "-journal"):
        Path(str(destination) + suffix).unlink(missing_ok=True)
