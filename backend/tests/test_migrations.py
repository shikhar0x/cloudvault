"""Migration tests: a clean database must be fully initializable from
Alembic migrations, and the ORM must match the migrated schema.

These tests use a dedicated scratch database (name contains "test" —
enforced by conftest) that is dropped and recreated here.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "database" / "migrations"

EXPECTED_TABLES = {"users", "folders", "files", "share_links"}

# The scratch database for migration tests.
_BASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://cloudvault:change_me@localhost:5432/cloudvault_test",
)


def _psycopg_url(sqlalchemy_url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgresql://"):
        if sqlalchemy_url.startswith(prefix):
            return "postgresql://" + sqlalchemy_url[len(prefix):]
    raise ValueError(f"Not a PostgreSQL URL: {sqlalchemy_url}")


def _admin_connection():
    admin_url = _psycopg_url(_BASE_URL).rsplit("/", 1)[0] + "/postgres"
    return psycopg.connect(admin_url, autocommit=True)


def _scratch_db_name() -> str:
    name = _BASE_URL.rsplit("/", 1)[-1].split("?")[0] + "_migration_check"
    assert "test" in name, "refusing to touch a non-test database"
    return name


@pytest.fixture()
def scratch_database():
    """Provide a truly empty scratch database for one test."""
    db_name = _scratch_db_name()
    with _admin_connection() as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
        conn.execute(f'CREATE DATABASE "{db_name}"')
    yield _BASE_URL.rsplit("/", 1)[0] + "/" + db_name
    with _admin_connection() as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(MIGRATIONS_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.attributes["configure_logger"] = False
    return cfg


def _run_upgrade(database_url: str) -> None:
    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.upgrade(_alembic_config(database_url), "head")
    finally:
        if old is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old


def _run_downgrade(database_url: str) -> None:
    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.downgrade(_alembic_config(database_url), "base")
    finally:
        if old is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old


class TestMigrations:
    def test_upgrade_head_creates_full_schema_from_empty_database(self, scratch_database):
        _run_upgrade(scratch_database)

        engine = create_engine(scratch_database)
        try:
            inspector = inspect(engine)
            tables = set(inspector.get_table_names())
            assert EXPECTED_TABLES <= tables, f"missing tables: {EXPECTED_TABLES - tables}"

            users_columns = {c["name"] for c in inspector.get_columns("users")}
            assert users_columns >= {"id", "name", "email", "password_hash", "created_at"}

            share_columns = {c["name"] for c in inspector.get_columns("share_links")}
            assert share_columns >= {"id", "file_id", "token", "expires_at", "created_at"}

            folder_columns = {c["name"] for c in inspector.get_columns("folders")}
            assert folder_columns >= {"id", "user_id", "parent_folder_id", "name", "created_at"}

            file_columns = {c["name"] for c in inspector.get_columns("files")}
            assert file_columns >= {
                "id", "user_id", "folder_id", "file_name",
                "object_key", "file_size", "mime_type", "created_at",
            }

            # Token lookups must be indexed.
            share_indexes = {i["name"] for i in inspector.get_indexes("share_links")}
            assert "ix_share_links_token" in share_indexes
        finally:
            engine.dispose()

    def test_application_can_use_migrated_database(self, scratch_database):
        """After migrating, the ORM can insert and query real rows."""
        _run_upgrade(scratch_database)

        from app.core.security import hash_password
        from app.database.models import File, ShareLink, User
        from app.database.base import utcnow

        engine = create_engine(scratch_database)
        try:
            from sqlalchemy.orm import Session

            with Session(engine) as session:
                user = User(name="Migration Check", email="mig@example.com",
                            password_hash=hash_password("SomePassword1!"))
                session.add(user)
                session.flush()
                file = File(user_id=user.id, file_name="m.pdf",
                            object_key="k", file_size=1, mime_type="application/pdf")
                session.add(file)
                session.flush()
                session.add(ShareLink(file_id=file.id, token="mig-token",
                                      expires_at=utcnow()))
                session.commit()

                stored = session.query(User).one()
                assert stored.email == "mig@example.com"
                assert stored.password_hash.startswith("$argon2id$")
        finally:
            engine.dispose()

    def test_orm_metadata_matches_migrated_schema(self, scratch_database):
        """The ORM models and the migration must describe the same schema."""
        _run_upgrade(scratch_database)

        from app.database.base import Base
        import app.database.models  # noqa: F401

        # Second scratch database built from metadata.create_all.
        orm_db_name = _scratch_db_name() + "_orm"
        with _admin_connection() as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{orm_db_name}" WITH (FORCE)')
            conn.execute(f'CREATE DATABASE "{orm_db_name}"')
        orm_url = _BASE_URL.rsplit("/", 1)[0] + "/" + orm_db_name
        orm_engine = create_engine(orm_url)
        try:
            Base.metadata.create_all(orm_engine)

            def snapshot(url: str):
                with psycopg.connect(_psycopg_url(url)) as conn:
                    columns = conn.execute(
                        "SELECT table_name, column_name, data_type, is_nullable, "
                        "column_default, character_maximum_length FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name <> 'alembic_version' "
                        "ORDER BY table_name, ordinal_position"
                    ).fetchall()
                    constraints = conn.execute(
                        "SELECT conname, contype, pg_get_constraintdef(c.oid) "
                        "FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
                        "JOIN pg_namespace n ON n.oid = t.relnamespace "
                        "WHERE n.nspname='public' AND t.relname <> 'alembic_version' "
                        "ORDER BY conname"
                    ).fetchall()
                    indexes = conn.execute(
                        "SELECT indexname, indexdef FROM pg_indexes "
                        "WHERE schemaname='public' AND tablename <> 'alembic_version' "
                        "ORDER BY indexname"
                    ).fetchall()
                return columns, constraints, indexes

            migrated = snapshot(scratch_database)
            from_orm = snapshot(orm_url)

            for label, migrated_part, orm_part in zip(
                ("columns", "constraints", "indexes"), migrated, from_orm
            ):
                assert migrated_part == orm_part, (
                    f"{label} differ between migrations and ORM:\n"
                    f"only in migrations: {set(migrated_part) - set(orm_part)}\n"
                    f"only in ORM: {set(orm_part) - set(migrated_part)}"
                )
        finally:
            orm_engine.dispose()
            with _admin_connection() as conn:
                conn.execute(f'DROP DATABASE IF EXISTS "{orm_db_name}" WITH (FORCE)')

    def test_downgrade_base_drops_everything(self, scratch_database):
        _run_upgrade(scratch_database)
        _run_downgrade(scratch_database)

        engine = create_engine(scratch_database)
        try:
            remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
            assert remaining == set(), f"tables survived downgrade: {remaining}"
        finally:
            engine.dispose()

    def test_upgrade_is_idempotent(self, scratch_database):
        _run_upgrade(scratch_database)
        _run_upgrade(scratch_database)  # must not fail or duplicate
        engine = create_engine(scratch_database)
        try:
            with engine.connect() as conn:
                versions = conn.execute(text("SELECT count(*) FROM alembic_version")).scalar_one()
                assert versions == 1
        finally:
            engine.dispose()
