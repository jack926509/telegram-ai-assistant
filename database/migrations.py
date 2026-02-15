from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations(database_url: str):
    """執行 Alembic migration 到最新版本"""
    project_root = Path(__file__).resolve().parent.parent
    alembic_ini = project_root / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(project_root / "database" / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(alembic_cfg, "head")
