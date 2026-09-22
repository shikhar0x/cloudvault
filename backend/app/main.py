"""CloudVault API application entry point.

Responsibilities are deliberately small: create the FastAPI app, load
configuration, register routers and middleware. Business logic lives in
the modules.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.database.session import get_engine
from app.modules.auth.router import router as auth_router
from app.modules.files.router import router as files_router
from app.modules.folders.router import router as folders_router
from app.modules.sharing.router import router as sharing_router
from app.modules.storage.router import router as storage_router


logger = logging.getLogger("cloudvault")

settings = get_settings()
settings.validate_production_safety()

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version="1.0.0",
    description="Cloud storage and sharing platform API.",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "cloudvault-api",
    }


@app.get("/api/health", tags=["health"], summary="Health check")
def health() -> dict[str, str]:
    """Liveness check that does not touch the database."""

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.get("/api/health/db", tags=["health"], summary="Database connectivity check")
def health_db() -> dict[str, str]:
    """Verify that the application can reach PostgreSQL."""

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Prevent raw SQLAlchemy errors from reaching API clients."""

    logger.exception(
        "Unhandled database error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


# Authentication
app.include_router(auth_router)

# Member 1 modules
app.include_router(files_router)
app.include_router(folders_router)
app.include_router(storage_router)

# Sharing
app.include_router(sharing_router)
