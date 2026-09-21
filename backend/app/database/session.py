"""Database engine and session management.

Provides:

- a lazily-created engine built from application configuration,
- a session factory (``SessionLocal``),
- the ``get_db`` FastAPI dependency used by every router.

Sessions are short-lived and scoped to a single request. No global
long-lived session is created anywhere in the application.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine = None
_session_factory: sessionmaker[Session] | None = None


def _database_url() -> str:
    """Return the configured database URL.

    ``pool_pre_ping`` keeps connections healthy across database restarts,
    which is common in local development.
    """
    return get_settings().DATABASE_URL


def get_engine():
    """Create the SQLAlchemy engine on first use and reuse it afterwards."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            _database_url(),
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the process-wide session factory (created lazily)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _session_factory


def create_session() -> Session:
    """Open a new database session. The caller is responsible for closing it."""
    return get_session_factory()()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session.

    The session is always closed when the request finishes; if the request
    failed with an unhandled error the transaction is rolled back.
    """
    db = create_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_engine() -> None:
    """Dispose the current engine and session factory.

    Used by the test suite to point the application at a dedicated test
    database; never needed in normal application code.
    """
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
