from pathlib import Path

from app.infrastructure.storage.interface import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, root: str = "storage"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, object_key: str) -> Path:
        path = self.root / object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def upload(self, file_object, object_key: str, content_type: str | None = None) -> None:
        path = self._path(object_key)

        with path.open("wb") as destination:
            while chunk := file_object.read(1024 * 1024):
                destination.write(chunk)

    def download(self, object_key: str):
        return self._path(object_key).open("rb")

    def delete(self, object_key: str) -> None:
        path = self._path(object_key)

        if path.exists():
            path.unlink()

    def exists(self, object_key: str) -> bool:
        return self._path(object_key).exists()
