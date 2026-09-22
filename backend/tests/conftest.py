"""Pytest configuration for the CloudVault backend tests.

Test database strategy
----------------------
- Tests run against a **dedicated PostgreSQL test database** — never the
  developer's real database. The test database is taken from
  ``TEST_DATABASE_URL`` (or ``DATABASE_URL``) and is *refused* unless its
  name clearly marks it as a test database (contains "test").
- The schema is created once per session by running the real Alembic
  migrations (``alembic upgrade head``) — the same way production is
  initialized. Tables are truncated between tests.
- The application itself is exercised through ``TestClient`` with its real
  ``get_db`` dependency pointing at the test database, so the tests cover
  the true wiring (engine, session, dependencies, routers).

Environment variables are set at import time, before any ``app`` import,
so application settings/engine caches pick them up.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
MIGRATIONS_DIR = REPO_ROOT / "database" / "migrations"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# --- Test environment (set BEFORE importing the application) ---------------
_TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://cloudvault:change_me@localhost:5433/cloudvault_test",
)
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-not-for-any-real-use"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["PUBLIC_SHARE_BASE_URL"] = "http://localhost:3000"

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402


def _psycopg_url(sqlalchemy_url: str) -> str:
    """Convert a SQLAlchemy URL to a plain psycopg connection URL."""
    for prefix in ("postgresql+psycopg://", "postgresql://"):
        if sqlalchemy_url.startswith(prefix):
            return "postgresql://" + sqlalchemy_url[len(prefix):]
    raise ValueError(f"Not a PostgreSQL URL: {sqlalchemy_url}")


def _database_name(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.rsplit("/", 1)[-1].split("?")[0]


def _ensure_test_database_exists() -> None:
    """Create the test database if it does not exist yet."""
    db_name = _database_name(_TEST_DATABASE_URL)
    if "test" not in db_name:
        raise pytest.UsageError(
            f"Refusing to run tests against database {db_name!r}: the name must "
            "contain 'test' so that a real database is never mutated. "
            "Set TEST_DATABASE_URL to a dedicated test database."
        )
    try:
        with psycopg.connect(_psycopg_url(_TEST_DATABASE_URL)):
            return
    except psycopg.OperationalError as exc:
        if exc.sqlstate != "3D000":  # 3D000 = invalid catalog name
            raise pytest.UsageError(
                f"Could not connect to the test PostgreSQL server: {exc}\n"
                "Start PostgreSQL (e.g. `docker compose up -d postgres`) and "
                "check TEST_DATABASE_URL."
            ) from exc

    # Database does not exist: try to create it via the maintenance DB.
    admin_url = _psycopg_url(_TEST_DATABASE_URL).rsplit("/", 1)[0] + "/postgres"
    try:
        with psycopg.connect(admin_url, autocommit=True) as conn:
            conn.execute(f'CREATE DATABASE "{db_name}"')
    except psycopg.Error as exc:
        raise pytest.UsageError(
            f"Test database {db_name!r} does not exist and could not be "
            f"created automatically: {exc}\nCreate it manually, e.g. "
            f"`CREATE DATABASE {db_name};`"
        ) from exc


def _run_migrations() -> None:
    """Initialize the test database schema with the real Alembic migrations."""
    cfg = Config(str(MIGRATIONS_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")


_ensure_test_database_exists()


from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database.models import File, Folder, ShareLink, User  # noqa: E402
from app.database.session import create_session, get_engine  # noqa: E402
from app.main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Session-scoped setup
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _migrated_schema():
    """Create the schema once per session via Alembic migrations."""
    _run_migrations()
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate all tables around every test for full isolation."""
    _truncate_all()
    yield
    _truncate_all()


def _truncate_all() -> None:
    with get_engine().begin() as conn:
        conn.execute(
            text("TRUNCATE TABLE share_links, files, folders, users CASCADE")
        )


# ---------------------------------------------------------------------------
# Reusable fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """A plain database session for arranging data directly through the ORM."""
    session = create_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """HTTP client bound to the real application and test database."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def make_user(db):
    """Factory: create a user with a properly hashed password."""

    def _make_user(*, email: str = "user@example.com", name: str = "Test User",
                   password: str = "Sup3rSecret!") -> User:
        user = User(name=name, email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make_user


@pytest.fixture()
def make_folder(db):
    """Factory: create a folder owned by a user."""

    def _make_folder(owner: User, name: str = "Folder",
                     parent: "Folder | None" = None) -> Folder:
        folder = Folder(
            user_id=owner.id,
            parent_folder_id=parent.id if parent else None,
            name=name,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    return _make_folder


@pytest.fixture()
def make_file(db):
    """Factory: create file metadata owned by ``owner`` (member-1 boundary)."""

    def _make_file(owner: User, *, file_name: str = "document.pdf",
                   folder: "Folder | None" = None) -> File:
        file = File(
            user_id=owner.id,
            folder_id=folder.id if folder else None,
            file_name=file_name,
            object_key=f"users/{owner.id}/{file_name}",
            file_size=1024,
            mime_type="application/pdf",
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        return file

    return _make_file


@pytest.fixture()
def make_share(db):
    """Factory: create a share link record directly (bypasses the API)."""

    def _make_share(file: File, *, token: str | None = None, expires_at=None) -> ShareLink:
        from datetime import timedelta

        from app.database.base import utcnow

        share = ShareLink(
            file_id=file.id,
            token=token or f"fixed-{uuid4().hex}",
            expires_at=expires_at or (utcnow() + timedelta(days=1)),
        )
        db.add(share)
        db.commit()
        db.refresh(share)
        return share

    return _make_share


@pytest.fixture()
def auth_headers():
    """Factory: Authorization header carrying a valid JWT for a user."""

    def _auth_headers(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}

    return _auth_headers


@pytest.fixture()
def register_and_login(client):
    """Factory: register + login through the API, return auth headers."""

    def _register_and_login(*, email: str = "flow@example.com",
                            password: str = "Sup3rSecret!") -> dict[str, str]:
        response = client.post(
            "/api/auth/register",
            json={"name": "Flow User", "email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _register_and_login
