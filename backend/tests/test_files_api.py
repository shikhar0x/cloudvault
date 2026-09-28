import io
import pytest
from fastapi.testclient import TestClient

from app.modules.auth.service import register_user


def test_file_upload_download_delete_flow(client: TestClient, db):
    user = register_user(db, name="File User", email="fileuser@test.com", password="password123")
    login_res = client.post("/api/auth/login", json={"email": "fileuser@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload file
    file_content = b"Hello, CloudVault storage!"
    upload_res = client.post(
        "/api/files/upload",
        files={"file": ("hello.txt", io.BytesIO(file_content), "text/plain")},
        headers=headers,
    )
    assert upload_res.status_code == 201
    file_data = upload_res.json()
    file_id = file_data["id"]
    assert file_data["file_name"] == "hello.txt"
    assert file_data["file_size"] == len(file_content)

    # 2. List files
    list_res = client.get("/api/files", headers=headers)
    assert list_res.status_code == 200
    files_list = list_res.json()
    assert len(files_list) == 1
    assert files_list[0]["id"] == file_id

    # 3. Download file
    download_res = client.get(f"/api/files/{file_id}/download", headers=headers)
    assert download_res.status_code == 200
    assert download_res.content == file_content

    # 4. Delete file
    del_res = client.delete(f"/api/files/{file_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify deleted
    get_res = client.get(f"/api/files/{file_id}", headers=headers)
    assert get_res.status_code == 404
