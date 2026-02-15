from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def run_migrations(database_url: str):
    """執行 Alembic migration 到最新版本"""
    project_root = Path(__file__).resolve().parent.parent
    alembic_ini = project_root / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(project_root / "database" / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    # 舊版部署可能已經有資料表，但沒有 alembic_version
    # 這種情況先標記為 0001，再升級到 head (0002+)
    engine = create_engine(database_url)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    has_legacy_tables = any(
        name in existing_tables for name in ("calendar_events", "expenses", "user_preferences")
    )
    has_alembic_version = "alembic_version" in existing_tables

    if has_legacy_tables and not has_alembic_version:
        command.stamp(alembic_cfg, "0001_initial_schema")

    command.upgrade(alembic_cfg, "head")
