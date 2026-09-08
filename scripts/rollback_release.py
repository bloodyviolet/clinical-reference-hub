#!/usr/bin/env python3
"""Failure-atomic rollback for the canonical /opt/medical-api/app layout."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.db_ops import (
    alembic_revision,
    backup_sqlite,
    restore_sqlite,
    sqlite_integrity,
    verify_backup_metadata,
)

CONFIRM = "ROLLBACK-SERVICE-STOPPED"


def read_env(path: Path) -> dict[str, str]:
    values = {}

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise RuntimeError(f"Invalid environment line: {raw!r}")

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def database_path(env: dict[str, str]) -> Path:
    url = env.get("MEDICAL_API_DATABASE_URL", "")
    prefix = "sqlite:///"

    if not url.startswith(prefix):
        raise RuntimeError(
            "Rollback requires an explicit SQLite database URL"
        )

    path = Path(url[len(prefix):])

    if not path.is_absolute():
        raise RuntimeError("SQLite database path must be absolute")

    return path


def release_python(release: Path) -> Path:
    python = release / ".venv" / "bin" / "python"

    if not python.is_file():
        raise RuntimeError(f"Release Python missing: {python}")

    return python


def release_head(release: Path) -> str:
    script = (
        "from pathlib import Path; import sys; "
        "sys.path.insert(0, str(Path.cwd())); "
        "import database; "
        "print(database.current_migration_head())"
    )

    result = subprocess.run(
        [str(release_python(release)), "-c", script],
        cwd=release,
        text=True,
        capture_output=True,
        check=True,
    )

    return result.stdout.strip().splitlines()[-1]


def validate_release(release: Path) -> None:
    required = (
        "alembic.ini",
        "main.py",
        "scripts/preflight.py",
        "scripts/prod_start.sh",
        ".venv/bin/python",
    )

    if not release.is_dir():
        raise RuntimeError(f"Release directory missing: {release}")

    missing = [
        item for item in required
        if not (release / item).is_file()
    ]

    if missing:
        raise RuntimeError(
            "Incomplete release: " + ", ".join(missing)
        )


def require_service_stopped(service: str) -> None:
    result = subprocess.run(
        [
            "systemctl", "show", service,
            "-p", "ActiveState", "--value",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    state = result.stdout.strip()

    if state not in {"inactive", "failed"}:
        raise RuntimeError(
            f"{service} must be stopped; ActiveState={state}"
        )


def preflight(
    release: Path,
    db: Path,
    base_env: dict[str, str],
) -> None:
    with tempfile.TemporaryDirectory(
        prefix="medical-api-rollback-preflight-"
    ) as raw:
        temp = Path(raw)
        probe = temp / "medical.db"

        shutil.copy2(db, probe)

        env = os.environ.copy()
        env.update(base_env)
        env["MEDICAL_API_DATABASE_URL"] = f"sqlite:///{probe}"
        env["MEDICAL_API_BACKUP_DIR"] = str(temp / "backups")
        env["MEDICAL_API_PYTHON"] = str(
            release_python(release)
        )

        result = subprocess.run(
            [
                str(release_python(release)),
                "scripts/preflight.py",
            ],
            cwd=release,
            env=env,
            text=True,
            capture_output=True,
        )

        if result.returncode:
            raise RuntimeError(
                "Release preflight failed:\n"
                + result.stdout
                + result.stderr
            )


def perform(
    target: Path,
    rollback_db: Path,
    app: Path,
    env_file: Path,
    service: str,
):
    target = target.absolute()
    rollback_db = rollback_db.absolute()
    app = app.absolute()

    validate_release(target)

    if not app.is_dir() or app.is_symlink():
        raise RuntimeError(
            f"Canonical app must be an ordinary directory: {app}"
        )

    if target == app:
        raise RuntimeError("Target cannot equal active application")

    if target.is_relative_to(app) or app.is_relative_to(target):
        raise RuntimeError(
            "Target and active application cannot contain each other"
        )

    if target.stat().st_dev != app.stat().st_dev:
        raise RuntimeError(
            "Target and active app must be on the same filesystem"
        )

    ok, detail = sqlite_integrity(rollback_db)
    if not ok:
        raise RuntimeError(f"Rollback DB integrity failed: {detail}")

    ok, detail = verify_backup_metadata(rollback_db)
    if not ok:
        raise RuntimeError(f"Rollback DB metadata failed: {detail}")

    target_revision = release_head(target)
    db_revision = alembic_revision(rollback_db)

    if db_revision != target_revision:
        raise RuntimeError(
            f"Rollback DB {db_revision!r} != release {target_revision!r}"
        )

    env = read_env(env_file)
    live_db = database_path(env)

    ok, detail = sqlite_integrity(live_db)
    if not ok:
        raise RuntimeError(f"Live DB integrity failed: {detail}")

    # Prove target code + target DB compatibility before mutation.
    preflight(target, rollback_db, env)

    # Final gate before touching active code or live DB.
    require_service_stopped(service)

    backup_dir = Path(env["MEDICAL_API_BACKUP_DIR"])

    safety, _ = backup_sqlite(
        live_db,
        backup_dir / "pre-rollback",
        prefix="pre-rollback",
        keep=10,
    )

    stamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    previous = app.parent / f".app-pre-rollback-{stamp}"

    if previous.exists():
        raise RuntimeError(f"Temporary path exists: {previous}")

    switched = False

    try:
        # Code first. DB remains untouched if this switch fails.
        os.replace(app, previous)

        try:
            os.replace(target, app)
        except BaseException:
            os.replace(previous, app)
            raise

        switched = True

        # Only now mutate the database.
        restore_sqlite(rollback_db, live_db)

        if alembic_revision(live_db) != target_revision:
            raise RuntimeError(
                "Restored database revision verification failed"
            )

        # Re-certify the new pair before accepting rollback.
        preflight(app, live_db, env)

        # Keep exactly one reversible code pair:
        # target now becomes the previously active application.
        os.replace(previous, target)
        switched = False

        return safety, target

    except BaseException:
        recovery_errors = []

        if switched:
            try:
                if app.exists() and not target.exists():
                    os.replace(app, target)

                if previous.exists():
                    os.replace(previous, app)

            except BaseException as exc:
                recovery_errors.append(
                    f"code recovery failed: {exc}"
                )

        try:
            restore_sqlite(safety, live_db)

        except BaseException as exc:
            recovery_errors.append(
                f"database recovery failed: {exc}"
            )

        if recovery_errors:
            raise RuntimeError(
                "ROLLBACK FAILED; AUTOMATIC RECOVERY INCOMPLETE: "
                + "; ".join(recovery_errors)
            )

        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Failure-atomic canonical Medical API rollback"
    )

    parser.add_argument("--target-release", type=Path, required=True)
    parser.add_argument("--database-backup", type=Path, required=True)

    parser.add_argument(
        "--app-path",
        type=Path,
        default=Path("/opt/medical-api/app"),
    )

    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("/etc/medical-api/medical-api.env"),
    )

    parser.add_argument(
        "--service-name",
        default="medical-api.service",
    )

    parser.add_argument("--confirm", required=True)

    args = parser.parse_args()

    if args.confirm != CONFIRM:
        parser.error(
            f'Pass --confirm "{CONFIRM}" only after stopping the API.'
        )

    safety, previous = perform(
        args.target_release,
        args.database_backup,
        args.app_path,
        args.env_file,
        args.service_name,
    )

    print(f"pre_rollback_backup={safety}")
    print(f"previous_code={previous}")
    print(
        "restored_revision="
        f"{alembic_revision(args.database_backup)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
