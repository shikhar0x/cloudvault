import pytest
from fastapi.testclient import TestClient

from app.database.models import User
from app.modules.auth.service import register_user


def test_folder_crud_flow(client: TestClient, db):
    user = register_user(db, name="Folder User", email="folder@test.com", password="password123")
    login_res = client.post("/api/auth/login", json={"email": "folder@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create root folder
    create_res = client.post(
        "/api/folders",
        json={"name": "Docs"},
        headers=headers,
    )
    assert create_res.status_code == 201
    folder_data = create_res.json()
    folder_id = folder_data["id"]
    assert folder_data["name"] == "Docs"
    assert folder_data["parent_folder_id"] is None

    # 2. Create subfolder
    sub_res = client.post(
        "/api/folders",
        json={"name": "Invoices", "parent_id": folder_id},
        headers=headers,
    )
    assert sub_res.status_code == 201
    sub_data = sub_res.json()
    sub_id = sub_data["id"]
    assert sub_data["parent_folder_id"] == folder_id

    # 3. List root folders
    list_res = client.get("/api/folders", headers=headers)
    assert list_res.status_code == 200
    root_folders = list_res.json()
    assert len(root_folders) == 1
    assert root_folders[0]["id"] == folder_id

    # 4. List subfolders
    sublist_res = client.get(f"/api/folders?parent_id={folder_id}", headers=headers)
    assert sublist_res.status_code == 200
    sub_folders = sublist_res.json()
    assert len(sub_folders) == 1
    assert sub_folders[0]["id"] == sub_id

    # 5. Delete folder
    del_res = client.delete(f"/api/folders/{folder_id}", headers=headers)
    assert del_res.status_code == 204

    # 6. Verify deleted
    get_res = client.get(f"/api/folders/{folder_id}", headers=headers)
    assert get_res.status_code == 404
