import io
import pytest
from fastapi.testclient import TestClient

from app.modules.auth.service import register_user


def test_storage_stats_flow(client: TestClient, db):
    user = register_user(db, name="Stats User", email="statsuser@test.com", password="password123")
    login_res = client.post("/api/auth/login", json={"email": "statsuser@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Initial stats
    stats_res = client.get("/api/storage/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["used_bytes"] == 0
    assert stats["file_count"] == 0
    assert stats["folder_count"] == 0

    # Upload a file
    content = b"Storage test data string"
    client.post(
        "/api/files/upload",
        files={"file": ("stats_file.txt", io.BytesIO(content), "text/plain")},
        headers=headers,
    )

    # Create a folder
    client.post("/api/folders", json={"name": "Test Folder"}, headers=headers)

    # Updated stats
    updated_res = client.get("/api/storage/stats", headers=headers)
    assert updated_res.status_code == 200
    updated_stats = updated_res.json()
    assert updated_stats["used_bytes"] == len(content)
    assert updated_stats["file_count"] == 1
    assert updated_stats["folder_count"] == 1
