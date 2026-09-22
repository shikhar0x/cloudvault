"""Sharing module models.

The canonical ``ShareLink`` model lives in the shared database model layer
(``app.database.models``) so that Alembic sees a single source of truth.
It is re-exported here for module-local imports.
"""

from app.database.models import ShareLink

__all__ = ["ShareLink"]
