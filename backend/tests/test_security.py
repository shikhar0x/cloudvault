"""Unit tests for password hashing and JWT handling (core/security.py)."""

from __future__ import annotations

import time
from datetime import timedelta
from uuid import uuid4

import pytest
from jose import jwt as jose_jwt

from app.core.config import get_settings
from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        password = "CorrectHorse42!"
        hashed = hash_password(password)
        assert hashed != password
        assert password not in hashed
        assert hashed.startswith("$argon2id$"), "must use Argon2id"

    def test_verify_roundtrip(self):
        password = "CorrectHorse42!"
        assert verify_password(password, hash_password(password)) is True

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("CorrectHorse42!")
        assert verify_password("wrong-password", hashed) is False

    def test_hashes_are_salted(self):
        """Two hashes of the same password must differ (random salt)."""
        assert hash_password("same-password") != hash_password("same-password")

    def test_verify_rejects_malformed_hash(self):
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_verify_rejects_empty_hash(self):
        assert verify_password("anything", "") is False


# ---------------------------------------------------------------------------
# JWT creation / validation
# ---------------------------------------------------------------------------

class TestJwt:
    def test_create_and_decode_roundtrip(self):
        subject = uuid4()
        token = create_access_token(subject)
        payload = decode_access_token(token)
        assert payload["sub"] == str(subject)
        assert payload["type"] == "access"
        assert "exp" in payload and "iat" in payload

    def test_token_carries_expiry(self):
        payload = decode_access_token(create_access_token(uuid4()))
        assert payload["exp"] > payload["iat"]

    def test_expired_token_rejected(self):
        token = create_access_token(uuid4(), expires_delta=timedelta(minutes=-1))
        with pytest.raises(ExpiredTokenError):
            decode_access_token(token)

    def test_token_expires_exactly_when_configured(self):
        settings = get_settings()
        before = int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        payload = decode_access_token(create_access_token(uuid4()))
        after = int(time.time()) + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert before <= payload["exp"] <= after

    def test_invalid_signature_rejected(self):
        token = create_access_token(uuid4())
        forged = jose_jwt.encode(
            jose_jwt.decode(token, key="", options={"verify_signature": False}),
            key="a-completely-different-secret",
            algorithm="HS256",
        )
        with pytest.raises(InvalidTokenError):
            decode_access_token(forged)

    def test_malformed_tokens_rejected(self):
        for bad in ["", "not-a-token", "a.b", "a.b.c.d", "&&&", "eyJhbGciOiJub25lIn0.e30."]:
            with pytest.raises(InvalidTokenError):
                decode_access_token(bad)

    def test_alg_none_attack_rejected(self):
        """A token claiming alg=none must never be accepted."""
        import base64
        import json

        def b64(data: dict) -> str:
            return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

        header = b64({"alg": "none", "typ": "JWT"})
        claims = b64({"sub": str(uuid4()), "exp": 9999999999})
        unsigned = f"{header}.{claims}."
        with pytest.raises(InvalidTokenError):
            decode_access_token(unsigned)

    def test_token_without_sub_rejected(self):
        settings = get_settings()
        claims = {"exp": int(time.time()) + 3600}
        token = jose_jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_token_without_exp_rejected(self):
        settings = get_settings()
        claims = {"sub": str(uuid4())}
        token = jose_jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_payload_contains_no_sensitive_data(self):
        """Only the minimum claims belong in the token."""
        payload = decode_access_token(create_access_token(uuid4()))
        forbidden = {"password", "password_hash", "aws_secret_access_key", "database_url"}
        assert forbidden.isdisjoint(payload.keys())
