# CloudVault — Authentication & Authorization

Implementation: `backend/app/core/security.py`,
`backend/app/core/dependencies.py`, `backend/app/modules/auth/`.

---

## 1. Registration flow

```text
POST /api/auth/register
        |
        v
Validate input (Pydantic schema)
        |
        v
Normalize email (trim + lowercase)
        |
        v
Check for existing account
        |--- exists ---> 409 Conflict
        v
Hash password with Argon2id
        |
        v
INSERT user row in PostgreSQL
        |--- unique violation (race) ---> rollback + 409
        v
201 Created  (safe fields only: id, name, email, created_at)
```

Guarantees:

- Passwords are never stored, logged or returned in plaintext.
- The stored `users.password_hash` is an Argon2id hash
  (`$argon2id$...`, salted, memory-hard).
- The response never includes `password` or `password_hash`.

## 2. Login flow

```text
POST /api/auth/login
        |
        v
Normalize email
        |
        v
Find user in PostgreSQL
        |--- not found ---> dummy Argon2 verification (timing equalization) ---> 401
        v
Verify password against stored Argon2id hash
        |--- mismatch ---> 401
        v
Create signed JWT (HS256, configured secret + expiry)
        |
        v
200 { access_token, token_type, user }
```

Guarantees:

- Unknown email and wrong password produce the **same** status code, message
  and similar timing — attackers cannot enumerate registered accounts.
- JWT claims contain only: `sub` (user id), `iat`, `exp`, `type`.
  Never passwords, AWS credentials or profile data.

## 3. Protected-request flow

```text
Request with "Authorization: Bearer <token>"
        |
        v
get_current_user dependency
        |
        v
Validate JWT: signature (algorithm pinned to config),
              expiration, required sub claim
        |--- invalid/expired ---> 401 with WWW-Authenticate: Bearer
        v
Load user from PostgreSQL by sub
        |--- user deleted since token issued ---> 401
        v
current_user available to the route
```

- `GET /api/auth/me` is the canonical protected endpoint — use it to verify
  tokens during development and integration.
- Identity **always** comes from the validated JWT. `user_id` values in
  request bodies or frontend state are never trusted.

## 4. Authorization (separate from authentication)

Authentication answers *who is the user*. Authorization answers *may this
user touch this resource*. Every protected files/folders/sharing operation
must verify ownership server-side:

```text
authenticate user (JWT)
        |
        v
load resource from PostgreSQL
        |
        v
resource.user_id == current_user.id ?
        |--- no ---> 403 Forbidden
        |--- resource missing ---> 404 Not Found
        v
allow
```

Reusable helper (used by the sharing module today, ready for Member 1's
files/folders modules):

```python
from app.core.dependencies import ensure_resource_owner

file = db.get(File, file_id)
if file is None:
    raise HTTPException(status_code=404, detail="File not found.")
ensure_resource_owner(file, current_user)   # raises 403 if not the owner
```

Project convention (documented in `docs/api/api.md`):

- resource does not exist → `404`
- resource exists but belongs to another user → `403`

## 5. Dependency usage for other modules

```python
from app.core.dependencies import ensure_resource_owner, get_current_user
from app.database.models import User
from app.database.session import get_db

@router.get("/files/{file_id}")
def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),   # 401 without valid JWT
    db: Session = Depends(get_db),
):
    file = db.get(File, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found.")
    ensure_resource_owner(file, current_user)         # 403 if not owned
    ...
```

## 6. Token security review

| Threat                          | Mitigation                                                        |
|---------------------------------|-------------------------------------------------------------------|
| Password leakage                | Argon2id hashing; hashes never leave the service layer            |
| User enumeration (login)        | Identical 401 message + dummy verification for unknown accounts   |
| Forged tokens                   | HS256 signature with `JWT_SECRET_KEY`; algorithm pinned server-side (`alg=none` rejected) |
| Missing expiry                  | `exp` required on every token (`require_exp`)                     |
| Stolen long-lived tokens        | `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60)                        |
| Deleted-account tokens          | User re-loaded from PostgreSQL on every request                   |
| Production misconfiguration     | Startup refuses placeholder/short JWT secrets in production       |
