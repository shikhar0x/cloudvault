"""All SQLAlchemy models in one importable place.

Importing this package registers every model with the declarative Base so
that ``Base.metadata`` (used by Alembic) is complete.
"""

from app.database.models.file import File
from app.database.models.folder import Folder
from app.database.models.share_link import ShareLink
from app.database.models.user import User

__all__ = ["File", "Folder", "ShareLink", "User"]
