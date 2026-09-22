"""API tests for registration, login and the protected /me endpoint."""

from __future__ import annotations

from datetime import timedelta

from app.core.security import create_access_token
from app.database.models import User

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_successful_registration(self, client, db):
        response = client.post(
            "/api/auth/register",
            json={"name": "Alice", "email": "alice@example.com", "password": "Sup3rSecret!"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["email"] == "alice@example.com"
        assert body["name"] == "Alice"
        assert body["id"]
        assert body["created_at"]
        # Safe representation only.
        assert "password" not in body
        assert "password_hash" not in body

        stored = db.query(User).filter_by(email="alice@example.com").one()
        assert stored.password_hash.startswith("$argon2id$")
        assert "Sup3rSecret!" not in stored.password_hash

    def test_duplicate_email_rejected(self, client):
        payload = {"name": "Alice", "email": "dup@example.com", "password": "Sup3rSecret!"}
        assert client.post("/api/auth/register", json=payload).status_code == 201
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_duplicate_email_case_insensitive_after_normalization(self, client):
        payload = {"name": "Alice", "email": "case@example.com", "password": "Sup3rSecret!"}
        assert client.post("/api/auth/register", json=payload).status_code == 201
        response = client.post(
            "/api/auth/register",
            json={"name": "Evil", "email": "CASE@Example.com", "password": "Sup3rSecret!"},
        )
        assert response.status_code == 409

    def test_invalid_email_rejected(self, client):
        response = client.post(
            "/api/auth/register",
            json={"name": "A", "email": "not-an-email", "password": "Sup3rSecret!"},
        )
        assert response.status_code == 422

    def test_short_password_rejected(self, client):
        response = client.post(
            "/api/auth/register",
            json={"name": "A", "email": "short@example.com", "password": "short"},
        )
        assert response.status_code == 422

    def test_missing_fields_rejected(self, client):
        response = client.post("/api/auth/register", json={"email": "x@example.com"})
        assert response.status_code == 422

    def test_empty_name_rejected(self, client):
        response = client.post(
            "/api/auth/register",
            json={"name": "   ", "email": "blank@example.com", "password": "Sup3rSecret!"},
        )
        assert response.status_code == 422

    def test_email_normalized_on_registration(self, client, db):
        response = client.post(
            "/api/auth/register",
            json={"name": "Mixed", "email": "  Mixed.Case@Example.COM  ",
                  "password": "Sup3rSecret!"},
        )
        assert response.status_code == 201
        assert response.json()["email"] == "mixed.case@example.com"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def _register(self, client, email="login@example.com", password="Sup3rSecret!"):
        response = client.post(
            "/api/auth/register",
            json={"name": "Login User", "email": email, "password": password},
        )
        assert response.status_code == 201

    def test_successful_login(self, client):
        self._register(client)
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "Sup3rSecret!"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["user"]["email"] == "login@example.com"
        assert "password_hash" not in body["user"]

    def test_login_normalizes_email(self, client):
        self._register(client)
        response = client.post(
            "/api/auth/login",
            json={"email": "LOGIN@example.com", "password": "Sup3rSecret!"},
        )
        assert response.status_code == 200

    def test_wrong_password_rejected(self, client):
        self._register(client)
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "WrongPassword1!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."

    def test_unknown_account_rejected_with_same_message(self, client):
        self._register(client)
        wrong_password = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "WrongPassword1!"},
        )
        unknown_account = client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "Whatever123!"},
        )
        assert wrong_password.status_code == unknown_account.status_code == 401
        # Identical error message: no user-enumeration oracle.
        assert wrong_password.json() == unknown_account.json()

    def test_malformed_login_rejected(self, client):
        response = client.post("/api/auth/login", json={"email": "login@example.com"})
        assert response.status_code == 422
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Protected endpoint: GET /api/auth/me
# ---------------------------------------------------------------------------

class TestCurrentUserEndpoint:
    def test_me_with_valid_token(self, client, make_user, auth_headers):
        user = make_user(email="me@example.com")
        response = client.get("/api/auth/me", headers=auth_headers(user))
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(user.id)
        assert body["email"] == "me@example.com"
        assert "password_hash" not in body

    def test_me_without_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert response.headers.get("www-authenticate") == "Bearer"

    def test_me_with_garbage_token(self, client):
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
        assert response.status_code == 401

    def test_me_with_expired_token(self, client, make_user, auth_headers):
        user = make_user(email="expired@example.com")
        token = create_access_token(user.id, expires_delta=timedelta(minutes=-5))
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_me_with_wrong_signature_token(self, client, make_user, auth_headers):
        user = make_user(email="forged@example.com")
        from jose import jwt as jose_jwt

        forged = jose_jwt.encode(
            {"sub": str(user.id), "exp": 9999999999},
            key="attacker-knows-a-different-secret",
            algorithm="HS256",
        )
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert response.status_code == 401

    def test_me_with_token_for_deleted_user(self, client, db, make_user, auth_headers):
        user = make_user(email="deleted@example.com")
        headers = auth_headers(user)
        db.delete(user)
        db.commit()
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    def test_me_rejects_non_bearer_scheme(self, client, make_user, auth_headers):
        user = make_user(email="scheme@example.com")
        token = create_access_token(user.id)
        response = client.get("/api/auth/me", headers={"Authorization": f"Basic {token}"})
        assert response.status_code == 401

    def test_token_for_one_user_cannot_impersonate_another(self, client, make_user, auth_headers):
        alice = make_user(email="alice-imp@example.com")
        bob = make_user(email="bob-imp@example.com")
        # Token issued for Alice must resolve to Alice — never Bob.
        response = client.get("/api/auth/me", headers=auth_headers(alice))
        assert response.json()["id"] == str(alice.id) != str(bob.id)
