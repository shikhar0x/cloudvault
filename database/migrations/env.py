"""Alembic migration environment.

Loads the application's SQLAlchemy metadata and database configuration so
migrations target the same database used by the application.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool


# Repository layout:
#   repository/
#   ├── backend/
#   └── database/migrations/env.py
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.core.config import get_settings  # noqa: E402
from app.database.base import Base  # noqa: E402
import app.database.models  # noqa: E402,F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def _database_url() -> str:
    """Resolve the database URL.

    CI/tests can provide DATABASE_URL directly through the environment.
    Otherwise use the application's normal configuration.
    """

    env_url = os.getenv("DATABASE_URL")

    if env_url:
        return env_url

    return get_settings().DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = _database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
