# CloudVault — Sharing & Link Expiry

Implementation: `backend/app/modules/sharing/` (router → service → database),
model in `backend/app/database/models/share_link.py`.

---

## 1. Share creation flow

```text
Owner (authenticated with JWT)
        |
        v
POST /api/shares { file_id, expires_in }
        |
        v
Verify the file belongs to the authenticated user
        |--- someone else's file ---> 403
        |--- file missing ----------> 404
        v
Validate expiry duration ("1h" | "1d" | "7d")
        |
        v
Generate secure token: secrets.token_urlsafe(32)   [256 bits, URL-safe]
        |
        v
Persist share_links row (token, file_id, expires_at)
        |--- token collision (unique index) ---> regenerate (retried automatically)
        v
201 { id, token, share_url, expires_at, created_at, file }
```

Security properties:

- The token is generated from a cryptographically secure random source. It is
  **never** derived from file ids, user ids, timestamps or counters.
- Ownership is checked against the JWT identity — a client-supplied
  `user_id` is never consulted.
- `expires_at` is computed server-side as a timezone-aware UTC timestamp.

## 2. Public access flow

```text
Anyone with the link
        |
        v
GET /api/shares/{token}          (no authentication — token is the credential)
        |
        v
Look up token (unique index)
        |--- unknown/malformed ---> 404
        v
Check expires_at (server-side, timezone-aware UTC)
        |--- expired ---> 410 Gone
        v
Verify referenced file still exists
        |--- deleted (should not happen: FK cascade) ---> 404
        v
200 { file: {file_name, mime_type, file_size}, expires_at, download_url }
```

## 3. Download flow (storage integration)

```text
GET /api/shares/{token}/download
        |
        v
Validate token + expiry (same checks as lookup) ---- expired ---> 410
        |
        v
Sharing service returns validated download info
    (file_id, object_key, file_name, mime_type, file_size)
        |
        v
StorageProvider.download(object_key)        <-- Member 1's abstraction
        |--- not implemented yet ---> 501 Not Implemented
        v
Streamed response with Content-Disposition/Content-Type/Content-Length
```

Authorization here is based on the **share token and its expiry**, never on
the owner's JWT — the recipient is anonymous by design.

## 4. Expiry behavior

- `share_links.expires_at` (TIMESTAMPTZ) is the single authoritative expiry.
- Every public access (`GET /api/shares/{token}` and
  `GET /api/shares/{token}/download`) re-checks expiry **server-side**:
  `expires_at < now(UTC)` → `410 Gone`.
- All comparisons use timezone-aware datetimes (never naive vs aware).
- Frontend hiding of expired links is never the security boundary.

What the recipient sees when a link expires:

```json
// 410 Gone
{ "detail": "This share link has expired." }
```

## 5. Consistency guarantees

- `share_links.file_id → files.id ON DELETE CASCADE`: deleting a file removes
  its share links immediately — stale links can never serve deleted files.
- Deleting a folder cascades to contained files and their share links.
- The token column has a unique index → lookups are efficient and duplicates
  impossible.

## 6. Integration contract for Member 1 (storage)

The sharing module deliberately does **not** implement object storage. The
boundary is:

```python
# backend/app/modules/sharing/service.py

@dataclass(frozen=True)
class ShareDownloadInfo:
    share_id, file_id, object_key, file_name, mime_type, file_size

def get_validated_download_info(db, token) -> ShareDownloadInfo: ...
def resolve_storage_provider():
    """Imports app.infrastructure.storage.get_storage_provider."""
```

Member 1 implements in `backend/app/infrastructure/storage/`:

```python
def get_storage_provider():
    return S3Storage(...)   # or LocalStorage(...) per STORAGE_PROVIDER

class S3Storage:
    def download(self, object_key: str):   # <- contract used by sharing
        ...  # return a binary stream of the object
```

While that module does not exist, `resolve_storage_provider()` raises
`StorageNotConfiguredError` and the public download endpoint returns `501`
after full token validation — a clean, testable integration point instead of
a parallel storage implementation.

## 7. Frontend contract (Member 2)

1. `POST /api/shares` with the JWT → receive `{ token, share_url, expires_at }`.
2. Show/copy `share_url` (default `http://localhost:3000/share/{token}`,
   configurable via `PUBLIC_SHARE_BASE_URL`) — or build your own URL from
   `token`.
3. Public share page (`/share/[token]`) calls
   `GET {API}/api/shares/{token}` and renders the safe file info.
4. Download button uses `{API}/api/shares/{token}/download`
   (`download_url` from the lookup response, prefixed with the API base URL).
5. Handle `410` with an "expired link" state and `404` with a
   "link not found" state.
