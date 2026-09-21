"""Security primitives: password hashing (Argon2id) and JWT handling.

Password rules
--------------
- Passwords are hashed with Argon2id (``argon2-cffi``) — never stored or
  logged in plaintext.
- Verification relies entirely on the hashing library, which compares
  hashes in constant time, avoiding common timing-attack mistakes.

JWT rules
---------
- Tokens are signed with the configured ``JWT_SECRET_KEY`` /
  ``JWT_ALGORITHM`` and always carry an ``exp`` claim.
- The payload contains only the minimum claims: subject (user id), issued
  time, expiry and token type. No password data, AWS credentials or other
  sensitive profile data is ever placed inside a token.
- Decoding validates signature, expiration and the required ``sub`` claim;
  malformed or expired tokens raise instead of being silently accepted.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

# Argon2id with the library's recommended defaults (t=3, m=64 MiB, p=4).
_password_hasher = PasswordHasher()

# A real Argon2 hash of a random throwaway value. Used to equalize the
# timing of login attempts for nonexistent accounts so that attackers
# cannot enumerate registered emails by measuring response times.
_DUMMY_PASSWORD_HASH = _password_hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored Argon2id hash.

    Returns ``False`` for a mismatch or a malformed stored hash; the
    comparison itself is performed by argon2-cffi in constant time.
    """
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        # A malformed stored hash can never authenticate successfully.
        return False


def dummy_verify() -> None:
    """Burn roughly the same time as a real password verification.

    Call this on login attempts for accounts that do not exist so that
    "unknown email" and "wrong password" take a similar amount of time.
    """
    try:
        _password_hasher.verify(_DUMMY_PASSWORD_HASH, "definitely-wrong")
    except (VerifyMismatchError, InvalidHashError):  # pragma: no cover - always raises
        pass


def create_access_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    """Create a signed JWT for the given subject (user id).

    ``expires_delta`` defaults to ``ACCESS_TOKEN_EXPIRE_MINUTES`` from
    configuration; tests may pass a custom (including negative) delta.
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    claims: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT.

    Validates the signature (using the configured algorithm only — the
    algorithm is never taken from the token itself), the expiration and
    the presence of a non-empty ``sub`` claim.

    Raises:
        ExpiredTokenError: the token's ``exp`` claim is in the past.
        InvalidTokenError: the token is malformed, has an invalid
            signature, or is missing required claims.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            # python-jose option names: require_* booleans. The algorithm is
            # pinned to the configured one and never taken from the token.
            options={"require_exp": True, "require_sub": True},
        )
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Token has expired") from exc
    except JWTError as exc:
        raise InvalidTokenError("Invalid authentication token") from exc

    if not payload.get("sub"):
        raise InvalidTokenError("Invalid authentication token")
    return payload


class ExpiredTokenError(Exception):
    """The JWT was well-formed but its ``exp`` claim is in the past."""


class InvalidTokenError(Exception):
    """The JWT is malformed, has a bad signature or is missing claims."""
