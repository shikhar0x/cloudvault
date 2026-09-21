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
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.database.session import get_engine
from app.modules.auth.router import router as auth_router
from app.modules.sharing.router import router as sharing_router

logger = logging.getLogger("cloudvault")

settings = get_settings()
settings.validate_production_safety()

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version="1.0.0",
    description="Cloud storage and sharing platform API (college mini project).",
    debug=settings.DEBUG,
)

# The frontend (Next.js dev server) calls this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(sharing_router, prefix="/api")


@app.get("/api/health", tags=["health"], summary="Health check")
def health() -> dict:
    """Liveness check (does not touch the database)."""
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.APP_ENV}


@app.get("/api/health/db", tags=["health"], summary="Database connectivity check")
def health_db() -> dict:
    """Verify the application can reach PostgreSQL."""
    from sqlalchemy import text

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Prevent raw SQLAlchemy errors/tracebacks from reaching clients.

    Expected database errors (duplicate email, FK violations, …) are
    handled meaningfully inside services; anything reaching this handler
    is unexpected and gets a generic 500 while the details are logged
    server-side.
    """
    logger.exception("Unhandled database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )
