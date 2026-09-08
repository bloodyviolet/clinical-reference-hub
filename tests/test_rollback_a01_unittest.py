import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import rollback_release
from scripts.db_ops import alembic_revision


def make_db(path: Path, revision: str) -> None:
    con = sqlite3.connect(path)

    try:
        con.execute(
            "CREATE TABLE alembic_version "
            "(version_num VARCHAR(32) NOT NULL)"
        )
        con.execute(
            "INSERT INTO alembic_version VALUES (?)",
            (revision,),
        )
        con.commit()

    finally:
        con.close()


def make_release(path: Path, marker: str) -> None:
    (path / "scripts").mkdir(
        parents=True,
        exist_ok=True,
    )

    (path / ".venv" / "bin").mkdir(
        parents=True,
        exist_ok=True,
    )

    for relative in (
        "alembic.ini",
        "main.py",
        "scripts/preflight.py",
        "scripts/prod_start.sh",
        ".venv/bin/python",
    ):
        file = path / relative
        file.write_text(
            "# disposable fixture\n",
            encoding="utf-8",
        )

    (path / "MARKER").write_text(
        marker,
        encoding="utf-8",
    )


def build_fixture(tmp_path: Path):
    app = tmp_path / "app"
    target = tmp_path / "rollback-target"

    make_release(app, "CURRENT")
    make_release(target, "ROLLBACK")

    live_db = tmp_path / "live.db"
    rollback_db = tmp_path / "rollback.db"

    make_db(live_db, "0007")
    make_db(rollback_db, "0006")

    backup_dir = tmp_path / "backups"

    env_file = tmp_path / "medical-api.env"
    env_file.write_text(
        "\n".join(
            (
                "MEDICAL_API_ENV=production",
                (
                    "MEDICAL_API_DATABASE_URL="
                    f"sqlite:///{live_db}"
                ),
                (
                    "MEDICAL_API_BACKUP_DIR="
                    f"{backup_dir}"
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        app,
        target,
        live_db,
        rollback_db,
        env_file,
        backup_dir,
    )


def common_patches():
    return (
        patch.object(
            rollback_release,
            "release_head",
            return_value="0006",
        ),
        patch.object(
            rollback_release,
            "require_service_stopped",
            return_value=None,
        ),
    )


def marker(path: Path) -> str:
    return (path / "MARKER").read_text(
        encoding="utf-8"
    )


def test_code_switch_failure_preserves_original_pair(
    tmp_path,
):
    (
        app,
        target,
        live_db,
        rollback_db,
        env_file,
        _,
    ) = build_fixture(tmp_path)

    real_replace = rollback_release.os.replace

    def injected_replace(src, dst):
        src = Path(src)
        dst = Path(dst)

        if src == target and dst == app:
            raise OSError(
                "injected target-to-app failure"
            )

        return real_replace(src, dst)

    head_patch, service_patch = common_patches()

    with (
        head_patch,
        service_patch,
        patch.object(
            rollback_release,
            "preflight",
            return_value=None,
        ),
        patch.object(
            rollback_release.os,
            "replace",
            side_effect=injected_replace,
        ),
    ):
        with pytest.raises(
            OSError,
            match="injected target-to-app failure",
        ):
            rollback_release.perform(
                target,
                rollback_db,
                app,
                env_file,
                "test.service",
            )

    assert marker(app) == "CURRENT"
    assert marker(target) == "ROLLBACK"
    assert alembic_revision(live_db) == "0007"


def test_post_database_failure_restores_original_pair(
    tmp_path,
):
    (
        app,
        target,
        live_db,
        rollback_db,
        env_file,
        backup_dir,
    ) = build_fixture(tmp_path)

    calls = {"count": 0}

    def injected_preflight(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 2:
            raise RuntimeError(
                "injected post-database failure"
            )

    head_patch, service_patch = common_patches()

    with (
        head_patch,
        service_patch,
        patch.object(
            rollback_release,
            "preflight",
            side_effect=injected_preflight,
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="injected post-database failure",
        ):
            rollback_release.perform(
                target,
                rollback_db,
                app,
                env_file,
                "test.service",
            )

    assert marker(app) == "CURRENT"
    assert marker(target) == "ROLLBACK"
    assert alembic_revision(live_db) == "0007"

    safety = list(
        (
            backup_dir /
            "pre-rollback"
        ).glob("pre-rollback-*.sqlite3")
    )

    assert len(safety) == 1
    assert alembic_revision(safety[0]) == "0007"


def test_success_swaps_code_pair_and_database(
    tmp_path,
):
    (
        app,
        target,
        live_db,
        rollback_db,
        env_file,
        _,
    ) = build_fixture(tmp_path)

    head_patch, service_patch = common_patches()

    with (
        head_patch,
        service_patch,
        patch.object(
            rollback_release,
            "preflight",
            return_value=None,
        ),
    ):
        safety, previous = rollback_release.perform(
            target,
            rollback_db,
            app,
            env_file,
            "test.service",
        )

    assert safety.is_file()
    assert previous == target

    assert marker(app) == "ROLLBACK"
    assert marker(target) == "CURRENT"

    assert alembic_revision(live_db) == "0006"
    assert alembic_revision(safety) == "0007"
