"""End-to-end integration test for the full Member 3 responsibility.

Real flow, real PostgreSQL, real HTTP wiring:

    Register -> Login -> JWT -> /auth/me -> owned file fixture
    -> create share link -> open public share -> verify expiry
    -> reject expired access

Member 1's storage boundary is mocked (``FakeStorageProvider``); everything
else — auth, JWT, database, sharing, expiry — is real.
"""

from __future__ import annotations

import io
from datetime import timedelta

from app.database.base import utcnow
from app.database.models import File, Folder, ShareLink, User
from app.database.session import create_session
from app.modules.sharing import service as share_service


class FakeStorageProvider:
    def __init__(self, content: bytes):
        self.content = content
        self.requested_keys: list[str] = []

    def download(self, object_key: str):
        self.requested_keys.append(object_key)
        return io.BytesIO(self.content)


def test_full_member3_flow(client, monkeypatch):
    # --- 1. Register -------------------------------------------------------
    email = "integration@example.com"
    password = "IntegrationPass1!"
    response = client.post(
        "/api/auth/register",
        json={"name": "Integration User", "email": "Integration@Example.COM", "password": password},
    )
    assert response.status_code == 201
    assert response.json()["email"] == email  # normalized

    # Password is hashed in PostgreSQL, never plaintext.
    db = create_session()
    try:
        user = db.query(User).filter_by(email=email).one()
        assert user.password_hash.startswith("$argon2id$")
        assert password not in user.password_hash

        # --- 2. Login ------------------------------------------------------
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert response.json()["token_type"] == "bearer"
        headers = {"Authorization": f"Bearer {token}"}

        # --- 3. JWT protects the API ----------------------------------------
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401

        # --- 4. /auth/me works with the real token ---------------------------
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == str(user.id)

        # --- 5. Owned file fixture (member-1 boundary: metadata only) --------
        folder = Folder(name="Integration", owner=user)
        db.add(folder)
        db.flush()
        file = File(
            user_id=user.id,
            folder_id=folder.id,
            file_name="integration-evidence.pdf",
            object_key=f"users/{user.id}/integration-evidence.pdf",
            file_size=2048,
            mime_type="application/pdf",
        )
        db.add(file)
        db.commit()
        db.refresh(file)

        # --- 6. Owner creates a share link ------------------------------------
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": "1h"},
            headers=headers,
        )
        assert response.status_code == 201
        share = response.json()
        token_value = share["token"]
        assert share["share_url"].endswith(f"/share/{token_value}")

        # --- 7. Public share opens without authentication ---------------------
        response = client.get(f"/api/shares/{token_value}")
        assert response.status_code == 200
        public = response.json()
        assert public["file"]["file_name"] == "integration-evidence.pdf"
        assert public["file"]["file_size"] == 2048
        assert "password_hash" not in str(public)

        # --- 8. Public download works through the storage boundary ------------
        fake_storage = FakeStorageProvider(b"%PDF-integration-test-content")
        monkeypatch.setattr(
            share_service, "resolve_storage_provider", lambda: fake_storage
        )
        response = client.get(f"/api/shares/{token_value}/download")
        assert response.status_code == 200
        assert response.content == b"%PDF-integration-test-content"
        assert fake_storage.requested_keys == [file.object_key]

        # --- 9. Verify expiration is stored and approaching --------------------
        stored_share = db.query(ShareLink).filter_by(token=token_value).one()
        assert stored_share.expires_at.tzinfo is not None
        remaining = (stored_share.expires_at - utcnow()).total_seconds()
        assert 0 < remaining <= 3600

        # --- 10. Reject expired access (both endpoints) -------------------------
        stored_share.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()

        response = client.get(f"/api/shares/{token_value}")
        assert response.status_code == 410
        response = client.get(f"/api/shares/{token_value}/download")
        assert response.status_code == 410
        assert fake_storage.requested_keys == [file.object_key], (
            "storage must not be contacted again after expiry"
        )

        # --- 11. Unknown tokens never grant access ------------------------------
        assert client.get("/api/shares/definitely-not-a-real-token").status_code == 404
        assert client.get("/api/shares/definitely-not-a-real-token/download").status_code == 404
    finally:
        db.close()


def test_second_user_cannot_share_first_users_file_flow(client):
    """Two full accounts: the second must not be able to share the first's file."""
    # First account registers + logs in.
    client.post("/api/auth/register", json={
        "name": "Victim", "email": "victim@example.com", "password": "VictimPass1!"})
    response = client.post("/api/auth/login", json={
        "email": "victim@example.com", "password": "VictimPass1!"})
    victim_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    db = create_session()
    try:
        victim = db.query(User).filter_by(email="victim@example.com").one()
        file = File(
            user_id=victim.id,
            file_name="victim-secret.txt",
            object_key=f"users/{victim.id}/victim-secret.txt",
            file_size=10,
            mime_type="text/plain",
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        file_id = str(file.id)
    finally:
        db.close()

    # Second account registers + logs in.
    client.post("/api/auth/register", json={
        "name": "Attacker", "email": "attacker@example.com", "password": "AttackerPass1!"})
    response = client.post("/api/auth/login", json={
        "email": "attacker@example.com", "password": "AttackerPass1!"})
    attacker_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    # Attacker tries to share the victim's file.
    response = client.post(
        "/api/shares", json={"file_id": file_id, "expires_in": "7d"},
        headers=attacker_headers,
    )
    assert response.status_code == 403

    # Victim can share it.
    response = client.post(
        "/api/shares", json={"file_id": file_id, "expires_in": "7d"},
        headers=victim_headers,
    )
    assert response.status_code == 201
