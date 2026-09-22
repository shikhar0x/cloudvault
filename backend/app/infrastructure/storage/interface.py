from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, file_object, object_key: str, content_type: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def download(self, object_key: str):
        raise NotImplementedError

    @abstractmethod
    def delete(self, object_key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, object_key: str) -> bool:
        raise NotImplementedError
