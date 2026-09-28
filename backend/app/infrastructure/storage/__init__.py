from functools import lru_cache

from app.core.config import get_settings
from app.infrastructure.storage.interface import StorageBackend
from app.infrastructure.storage.local import LocalStorage
from app.infrastructure.storage.s3 import S3Storage


@lru_cache
def get_storage_provider() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_PROVIDER.lower() == "s3":
        return S3Storage()
    return LocalStorage(root="storage")


__all__ = ["StorageBackend", "LocalStorage", "S3Storage", "get_storage_provider"]
