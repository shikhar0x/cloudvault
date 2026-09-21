# CloudVault — API Contract

Base URL (development): `http://localhost:8000`

All request/response bodies are JSON. Errors use FastAPI's standard shape:

```json
{ "detail": "Human-readable message." }
```

Validation errors (schema problems) return `422` with a `detail` list in
FastAPI's default format.

## Status-code conventions

| Code | Meaning                                                                |
|------|------------------------------------------------------------------------|
| 200  | Success                                                                |
| 201  | Resource created                                                       |
| 400/422 | Invalid request (422 = schema validation, 400 = semantic rejection) |
| 401  | Not authenticated (missing/invalid/expired token)                       |
| 403  | Authenticated but not allowed (e.g. not the owner of a resource)        |
| 404  | Resource not found                                                      |
| 409  | Conflict (e.g. duplicate email)                                         |
| 410  | Share link has expired                                                  |
| 500  | Unexpected server error (details are logged server-side, not leaked)    |
| 501  | Valid share token but storage integration is not configured yet         |

**Ownership convention**: a resource that does not exist → `404`; a resource
that exists but belongs to somebody else → `403`.

---

## Authentication

Authenticated endpoints require:

```text
Authorization: Bearer <access_token>
```

The token is the JWT returned by `POST /api/auth/login`. Identity is **always**
derived from the validated JWT — `user_id` values supplied in request bodies
are never trusted for access decisions.

---

## 1. POST `/api/auth/register`

Create an account. **Public.**

Request:

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "Sup3rSecret!"
}
```

Validation:

- `name`: 1–255 characters (trimmed)
- `email`: valid email; normalized to lowercase/trimmed before storage
- `password`: 8–128 characters

Response `201`:

```json
{
  "id": "3f9c2b4e-...",
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2026-09-21T10:00:00.000000Z"
}
```

Errors:

- `409` — an account with this email already exists (case-insensitive)
- `422` — invalid/missing fields

The response never contains the password or its hash.

---

## 2. POST `/api/auth/login`

Exchange credentials for an access token. **Public.**

Request:

```json
{
  "email": "alice@example.com",
  "password": "Sup3rSecret!"
}
```

Response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "3f9c2b4e-...",
    "name": "Alice",
    "email": "alice@example.com",
    "created_at": "2026-09-21T10:00:00.000000Z"
  }
}
```

Errors:

- `401` — `{"detail": "Invalid email or password."}` — the same message and
  status for unknown emails and wrong passwords (no user-enumeration oracle)
- `422` — malformed body

JWT details: signed HS256 with `JWT_SECRET_KEY`, expires after
`ACCESS_TOKEN_EXPIRE_MINUTES` (default 60). Claims: `sub` (user id), `iat`,
`exp`, `type: "access"` — nothing sensitive.

---

## 3. GET `/api/auth/me`

Current user profile. **Requires authentication.**

Response `200`:

```json
{
  "id": "3f9c2b4e-...",
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2026-09-21T10:00:00.000000Z"
}
```

Errors: `401` (no token / malformed / expired / user deleted).

---

## 4. POST `/api/shares`

Create a share link for a file. **Requires authentication.**

Request:

```json
{
  "file_id": "8d1f0a2c-...",
  "expires_in": "1d"
}
```

- `file_id` — UUID of one of **your own** files
- `expires_in` — one of `"1h"`, `"1d"` (default), `"7d"`

Response `201`:

```json
{
  "id": "b2e77a10-...",
  "token": "VB_bpm76lhlTfXdV-Owoq5mZ3bg9n4aublOZLoaW0Ro",
  "share_url": "http://localhost:3000/share/VB_bpm76...",
  "expires_at": "2026-09-22T10:05:00.000000Z",
  "created_at": "2026-09-21T10:05:00.000000Z",
  "file": {
    "id": "8d1f0a2c-...",
    "file_name": "report.pdf",
    "mime_type": "application/pdf",
    "file_size": 248320
  }
}
```

Notes:

- `token` is generated with `secrets.token_urlsafe(32)` — 256 bits of entropy,
  URL-safe, unique (unique DB index; collisions are retried automatically).
- `share_url` points at the frontend share page and is built from
  `PUBLIC_SHARE_BASE_URL` (configurable, never hardcoded hostnames).
- Frontend can alternatively build its own URL from `token`.

Errors:

- `401` — not authenticated
- `403` — the file exists but belongs to another user
- `404` — no file with this id
- `422` — invalid body / unsupported `expires_in`

---

## 5. GET `/api/shares/{token}`

Public share information. **Public — the token itself is the credential.**

Response `200`:

```json
{
  "file": {
    "id": "8d1f0a2c-...",
    "file_name": "report.pdf",
    "mime_type": "application/pdf",
    "file_size": 248320
  },
  "expires_at": "2026-09-22T10:05:00.000000Z",
  "download_url": "/api/shares/VB_bpm76.../download"
}
```

`download_url` is relative — prefix it with the API base URL
(`NEXT_PUBLIC_API_URL`, e.g. `http://localhost:8000`).

Only safe public information is returned: no owner email, no password data,
no `object_key`, no internal ids beyond the file id.

Errors:

- `404` — unknown/malformed token, or the shared file no longer exists
- `410` — `{"detail": "This share link has expired."}`

---

## 6. GET `/api/shares/{token}/download`

Download the shared file. **Public — authorized by the share token and its
expiry, not by the owner's JWT.**

Success `200`: the file content streamed with:

```text
Content-Type: <file mime_type>
Content-Disposition: attachment; filename="<file_name>"
Content-Length: <file_size>
```

Errors:

- `404` — unknown token / file deleted
- `410` — expired token (checked server-side before storage is contacted)
- `501` — the token is valid but the storage integration
  (`app/infrastructure/storage`, Member 1) is not configured yet

### Storage integration contract (Member 1)

The sharing service validates the token and expiry, then delegates object
retrieval to the storage provider:

```python
from app.modules.sharing import service as share_service

info = share_service.get_validated_download_info(db, token)
# info.object_key, info.file_name, info.mime_type, info.file_size, info.file_id

provider = share_service.resolve_storage_provider()
stream = provider.download(info.object_key)   # binary stream
```

Member 1 implements `get_storage_provider()` in
`app/infrastructure/storage/` (see `docs/architecture/sharing.md`); until it
exists, `resolve_storage_provider()` raises `StorageNotConfiguredError` and
the endpoint returns `501` after full token validation.

---

## 7. Health

- `GET /api/health` — liveness (`{"status": "ok", ...}`)
- `GET /api/health/db` — verifies PostgreSQL connectivity

---

## Error-handling guarantees

- No raw SQLAlchemy tracebacks are ever returned (a global handler maps
  unexpected database errors to a generic `500` and logs details server-side).
- Services never swallow exceptions silently (`except: pass` is forbidden by
  project rules).
- Expired-share rejection happens **server-side** on every access; the
  frontend hiding expired links is never the security boundary.
