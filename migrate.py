"""Convenience entry point for upgrading the persisted SQLite schema."""
from pathlib import Path

from alembic import command
from alembic.config import Config

BASE_DIR = Path(__file__).resolve().parent


def migrate() -> None:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    command.upgrade(config, "head")


if __name__ == "__main__":
    migrate()
