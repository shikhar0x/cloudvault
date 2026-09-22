"""Sharing API tests: creation, tokens, public lookup, expiry, download."""

from __future__ import annotations

import io
import re
from datetime import timedelta

import pytest

from app.database.base import utcnow
from app.database.models import ShareLink
from app.modules.sharing import service as share_service

URLSAFE_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


# ---------------------------------------------------------------------------
# Share creation
# ---------------------------------------------------------------------------

class TestShareCreation:
    def test_create_share_returns_full_contract(self, client, make_user, make_file, auth_headers):
        owner = make_user(email="share-owner@example.com")
        file = make_file(owner, file_name="share-me.pdf")
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": "7d"},
            headers=auth_headers(owner),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["token"]
        assert body["share_url"].endswith(f"/share/{body['token']}")
        assert body["file"]["file_name"] == "share-me.pdf"
        assert body["file"]["mime_type"] == "application/pdf"
        assert body["file"]["file_size"] == 1024
        assert body["created_at"]
        assert body["expires_at"] > body["created_at"]
        # Internal fields must not leak.
        assert "object_key" not in body
        assert "password_hash" not in str(body)

    @pytest.mark.parametrize("expires_in,delta_hours", [("1h", 1), ("1d", 24), ("7d", 168)])
    def test_expiry_durations(self, client, make_user, make_file, auth_headers,
                              expires_in, delta_hours):
        owner = make_user(email=f"expiry-{expires_in}@example.com")
        file = make_file(owner)
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": expires_in},
            headers=auth_headers(owner),
        )
        assert response.status_code == 201
        from datetime import datetime

        created = datetime.fromisoformat(response.json()["created_at"])
        expires = datetime.fromisoformat(response.json()["expires_at"])
        actual_hours = (expires - created).total_seconds() / 3600
        assert abs(actual_hours - delta_hours) < 0.01

    def test_invalid_expiry_value_rejected(self, client, make_user, make_file, auth_headers):
        owner = make_user(email="bad-expiry@example.com")
        file = make_file(owner)
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": "30d"},
            headers=auth_headers(owner),
        )
        assert response.status_code == 422

    def test_missing_file_id_rejected(self, client, make_user, auth_headers):
        owner = make_user(email="no-file-id@example.com")
        response = client.post("/api/shares", json={}, headers=auth_headers(owner))
        assert response.status_code == 422

    def test_authentication_required(self, client, make_user, make_file):
        owner = make_user(email="unauth-share@example.com")
        file = make_file(owner)
        response = client.post("/api/shares", json={"file_id": str(file.id)})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token security
# ---------------------------------------------------------------------------

class TestTokenSecurity:
    def test_token_is_non_empty_and_url_safe(self, client, make_user, make_file, auth_headers):
        owner = make_user(email="token-safe@example.com")
        file = make_file(owner)
        body = client.post(
            "/api/shares", json={"file_id": str(file.id)}, headers=auth_headers(owner)
        ).json()
        token = body["token"]
        assert token
        assert URLSAFE_RE.match(token), "token must be URL-safe"
        assert len(token) >= 32, "token must be long (>= 32 chars ≈ 192 bits)"

    def test_tokens_are_unique_and_unpredictable(self, client, make_user, make_file, auth_headers):
        owner = make_user(email="token-unique@example.com")
        file = make_file(owner)
        tokens = set()
        for _ in range(10):
            response = client.post(
                "/api/shares", json={"file_id": str(file.id)}, headers=auth_headers(owner)
            )
            assert response.status_code == 201
            tokens.add(response.json()["token"])
        assert len(tokens) == 10, "every share must receive a fresh token"

    def test_token_not_derived_from_predictable_inputs(self, client, make_user, make_file, auth_headers):
        """Two different files for the same user at the same moment must get
        unrelated tokens (no file-id/user-id/timestamp derivation)."""
        owner = make_user(email="token-entropy@example.com")
        file_a = make_file(owner, file_name="a.txt")
        file_b = make_file(owner, file_name="b.txt")
        token_a = client.post(
            "/api/shares", json={"file_id": str(file_a.id)}, headers=auth_headers(owner)
        ).json()["token"]
        token_b = client.post(
            "/api/shares", json={"file_id": str(file_b.id)}, headers=auth_headers(owner)
        ).json()["token"]
        assert token_a != token_b
        # UUIDs of the files must not appear inside the tokens.
        assert str(file_a.id) not in token_a
        assert str(owner.id) not in token_a

    def test_token_collision_is_retried(self, client, db, monkeypatch, make_user, make_file, auth_headers):
        """If a generated token collides with an existing one, the service
        regenerates instead of failing."""
        owner = make_user(email="token-collision@example.com")
        file = make_file(owner)
        existing = ShareLink(file_id=file.id, token="collision-token",
                             expires_at=utcnow() + timedelta(days=1))
        db.add(existing)
        db.commit()

        calls = iter(["collision-token", "fresh-token-xyz"])
        monkeypatch.setattr(share_service, "generate_share_token", lambda: next(calls))

        response = client.post(
            "/api/shares", json={"file_id": str(file.id)}, headers=auth_headers(owner)
        )
        assert response.status_code == 201
        assert response.json()["token"] == "fresh-token-xyz"


# ---------------------------------------------------------------------------
# Public share lookup
# ---------------------------------------------------------------------------

class TestPublicShareLookup:
    def test_valid_share_lookup_public(self, client, make_user, make_file, make_share):
        owner = make_user(email="public-owner@example.com")
        file = make_file(owner, file_name="public-file.pdf")
        share = make_share(file)
        response = client.get(f"/api/shares/{share.token}")  # no auth headers
        assert response.status_code == 200
        body = response.json()
        assert body["file"]["file_name"] == "public-file.pdf"
        assert body["file"]["mime_type"] == "application/pdf"
        assert body["file"]["file_size"] == 1024
        assert body["download_url"].endswith(f"/api/shares/{share.token}/download")
        # Only safe public fields.
        assert "object_key" not in body["file"]
        assert "user_id" not in body["file"]
        assert "password_hash" not in str(body)

    def test_unknown_token_returns_404(self, client):
        response = client.get("/api/shares/no-such-token-123")
        assert response.status_code == 404

    def test_malformed_token_returns_404(self, client):
        response = client.get("/api/shares/%20%21%27%3B--bad")
        assert response.status_code == 404

    def test_sql_injection_token_is_harmless(self, client, db, make_user, make_file):
        owner = make_user(email="sqli@example.com")
        file = make_file(owner)
        db.add(ShareLink(file_id=file.id, token="legit",
                         expires_at=utcnow() + timedelta(days=1)))
        db.commit()

        response = client.get("/api/shares/legit%27%3B%20DROP%20TABLE%20share_links%3B--")
        assert response.status_code == 404
        # Table still intact.
        from sqlalchemy import text

        from app.database.session import get_engine

        with get_engine().connect() as conn:
            assert conn.execute(text("SELECT count(*) FROM share_links")).scalar_one() == 1

    def test_expired_share_lookup_returns_410(self, client, make_user, make_file, make_share):
        owner = make_user(email="expired-lookup@example.com")
        file = make_file(owner)
        share = make_share(file, expires_at=utcnow() - timedelta(minutes=1))
        response = client.get(f"/api/shares/{share.token}")
        assert response.status_code == 410
        assert "expired" in response.json()["detail"].lower()

    def test_expiry_boundary_is_inclusive(self, client, make_user, make_file, make_share):
        """A share expiring exactly now is already expired (server-side clock)."""
        owner = make_user(email="boundary@example.com")
        file = make_file(owner)
        share = make_share(file, expires_at=utcnow() - timedelta(seconds=1))
        assert client.get(f"/api/shares/{share.token}").status_code == 410


# ---------------------------------------------------------------------------
# Public download (storage boundary mocked)
# ---------------------------------------------------------------------------

class FakeStorageProvider:
    """Deterministic stand-in for Member 1's storage provider."""

    def __init__(self, content: bytes = b"fake file content"):
        self.content = content
        self.requested_keys: list[str] = []

    def download(self, object_key: str):
        self.requested_keys.append(object_key)
        return io.BytesIO(self.content)


@pytest.fixture()
def fake_storage(monkeypatch):
    provider = FakeStorageProvider()

    def _resolve():
        return provider

    monkeypatch.setattr(share_service, "resolve_storage_provider", _resolve)
    return provider


class TestPublicDownload:
    def test_valid_token_downloads_file(self, client, fake_storage, make_user, make_file, make_share):
        owner = make_user(email="download-owner@example.com")
        file = make_file(owner, file_name="download.bin")
        share = make_share(file)
        response = client.get(f"/api/shares/{share.token}/download")
        assert response.status_code == 200
        assert response.content == b"fake file content"
        assert fake_storage.requested_keys == [file.object_key]
        assert response.headers["content-disposition"] == 'attachment; filename="download.bin"'
        assert response.headers["content-type"].startswith("application/pdf")

    def test_expired_token_rejected_for_download(self, client, fake_storage, make_user, make_file, make_share):
        owner = make_user(email="expired-download@example.com")
        file = make_file(owner)
        share = make_share(file, expires_at=utcnow() - timedelta(hours=2))
        response = client.get(f"/api/shares/{share.token}/download")
        assert response.status_code == 410
        assert fake_storage.requested_keys == [], "storage must not be touched for expired links"

    def test_unknown_token_rejected_for_download(self, client, fake_storage):
        response = client.get("/api/shares/unknown-token/download")
        assert response.status_code == 404
        assert fake_storage.requested_keys == []

    def test_download_requires_no_authentication(self, client, fake_storage, make_user, make_file, make_share):
        """The share token itself is the credential — public by design."""
        owner = make_user(email="public-download@example.com")
        file = make_file(owner)
        share = make_share(file)
        response = client.get(f"/api/shares/{share.token}/download")
        assert response.status_code == 200

    def test_download_without_storage_integration_returns_501(
        self, client, monkeypatch, make_user, make_file, make_share
    ):
        """Until Member 1's storage layer lands, the integration point reports
        501 instead of pretending to work."""
        from app.modules.sharing.service import StorageNotConfiguredError

        def _raise():
            raise StorageNotConfiguredError("not implemented")

        monkeypatch.setattr(share_service, "resolve_storage_provider", _raise)
        owner = make_user(email="nostorage@example.com")
        file = make_file(owner)
        share = make_share(file)
        response = client.get(f"/api/shares/{share.token}/download")
        assert response.status_code == 501
        assert "storage" in response.json()["detail"].lower()

    def test_deleted_file_makes_share_inaccessible(self, client, db, fake_storage,
                                                   make_user, make_file, make_share):
        """Deleting a file removes its share links (FK cascade) — a stale link
        must not keep serving the file."""
        owner = make_user(email="deleted-file@example.com")
        file = make_file(owner)
        share = make_share(file)
        token = share.token

        db.delete(file)
        db.commit()

        assert client.get(f"/api/shares/{token}").status_code == 404
        assert client.get(f"/api/shares/{token}/download").status_code == 404
