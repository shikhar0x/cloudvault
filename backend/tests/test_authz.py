"""Authorization tests.

Authentication answers "who is the user?"; authorization answers "is this
user allowed to touch this resource?". These tests verify the ownership
foundation that Member 1's files/folders modules will reuse:

    authenticate user -> load resource -> resource.user_id == user.id
                                            -> allow / reject
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.dependencies import ensure_resource_owner


class TestEnsureResourceOwnerUnit:
    def test_owner_allowed(self, make_user, make_file):
        user = make_user(email="owner-unit@example.com")
        file = make_file(user)
        assert ensure_resource_owner(file, user) is file

    def test_non_owner_rejected_with_403(self, make_user, make_file):
        alice = make_user(email="alice-unit@example.com")
        mallory = make_user(email="mallory-unit@example.com")
        file = make_file(alice)
        with pytest.raises(HTTPException) as excinfo:
            ensure_resource_owner(file, mallory)
        assert excinfo.value.status_code == 403

    def test_resource_without_user_id_rejected(self, make_user):
        user = make_user(email="anon-unit@example.com")

        class Weird:
            pass

        with pytest.raises(HTTPException):
            ensure_resource_owner(Weird(), user)


class TestOwnershipThroughApi:
    """Ownership enforced end-to-end via the sharing endpoint."""

    def test_user_can_share_own_file(self, client, make_user, make_file, auth_headers):
        alice = make_user(email="alice-own@example.com")
        file = make_file(alice)
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": "1d"},
            headers=auth_headers(alice),
        )
        assert response.status_code == 201

    def test_user_cannot_share_someone_elses_file(self, client, make_user, make_file, auth_headers):
        alice = make_user(email="alice-victim@example.com")
        mallory = make_user(email="mallory-attacker@example.com")
        file = make_file(alice)
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": "1d"},
            headers=auth_headers(mallory),
        )
        assert response.status_code == 403
        # And no share link was created.
        from app.database.models import ShareLink

        from app.database.session import create_session

        db = create_session()
        try:
            assert db.query(ShareLink).filter_by(file_id=file.id).count() == 0
        finally:
            db.close()

    def test_sharing_missing_file_returns_404(self, client, make_user, auth_headers):
        import uuid

        user = make_user(email="missing-file@example.com")
        response = client.post(
            "/api/shares",
            json={"file_id": str(uuid.uuid4()), "expires_in": "1d"},
            headers=auth_headers(user),
        )
        assert response.status_code == 404

    def test_unauthenticated_user_cannot_create_shares(self, client, make_user, make_file):
        alice = make_user(email="noauth-share@example.com")
        file = make_file(alice)
        response = client.post(
            "/api/shares",
            json={"file_id": str(file.id), "expires_in": "1d"},
        )
        assert response.status_code == 401

    def test_request_body_cannot_override_jwt_identity(self, client, make_user, make_file, auth_headers):
        """A user_id in the request body must never influence ownership."""
        alice = make_user(email="alice-jwt@example.com")
        mallory = make_user(email="mallory-jwt@example.com")
        file = make_file(alice)

        # Mallory claims to be Alice via the body.
        response = client.post(
            "/api/shares",
            json={
                "file_id": str(file.id),
                "expires_in": "1d",
                "user_id": str(alice.id),
            },
            headers=auth_headers(mallory),
        )
        assert response.status_code == 403, "body-supplied user_id must not grant access"

        # Alice sharing her own file while claiming to be Mallory still works —
        # identity comes from the JWT, extra body fields are ignored.
        response = client.post(
            "/api/shares",
            json={
                "file_id": str(file.id),
                "expires_in": "1d",
                "user_id": str(mallory.id),
            },
            headers=auth_headers(alice),
        )
        assert response.status_code == 201
        from app.database.models import ShareLink

        from app.database.session import create_session

        db = create_session()
        try:
            share = db.query(ShareLink).one()
            assert share.file.user_id == alice.id
        finally:
            db.close()

    def test_jwt_for_one_user_never_grants_anothers_resources(self, client, make_user, make_file, auth_headers):
        """Covering the general pattern with two users and two files."""
        alice = make_user(email="alice-two@example.com")
        bob = make_user(email="bob-two@example.com")
        alice_file = make_file(alice, file_name="alice-secret.txt")
        bob_file = make_file(bob, file_name="bob-secret.txt")

        # Bob's token on Bob's file: allowed.
        assert client.post(
            "/api/shares",
            json={"file_id": str(bob_file.id)},
            headers=auth_headers(bob),
        ).status_code == 201

        # Bob's token on Alice's file: rejected.
        assert client.post(
            "/api/shares",
            json={"file_id": str(alice_file.id)},
            headers=auth_headers(bob),
        ).status_code == 403
