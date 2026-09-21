"""Folders module models (owned by Member 1).

The canonical ``Folder`` model lives in the shared database model layer
(``app.database.models``) so that Alembic sees a single source of truth.
It is re-exported here for Member 1's module-local imports.
"""

from app.database.models import Folder

__all__ = ["Folder"]
